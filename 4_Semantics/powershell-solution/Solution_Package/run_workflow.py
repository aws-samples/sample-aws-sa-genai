#!/usr/bin/env python3
"""
Snowflake → QuickSight interactive workflow

Runs all six steps from a single script:
  1. AWS setup  (region, account ID)
  2. Select or create a QuickSight Snowflake data source
  3. Generate dataset schema from the Snowflake DDL CSV
  4. Create / replace the QuickSight dataset
  5. Start and monitor SPICE ingestion
  6. Share the dataset with a QuickSight user (optional)

Usage:
    python run_workflow.py
    python run_workflow.py --region us-west-2
"""

import argparse
import boto3
import json
import os
import sys
import time

from generate_quicksight_schema import SnowflakeDDLParser, QuickSightSchemaGenerator

# ── ANSI colours (same as full-solution) ─────────────────────────────────────
GREEN  = '\033[0;32m'
RED    = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE   = '\033[0;34m'
BOLD   = '\033[1m'
RESET  = '\033[0m'

def ok(msg):    print(f"  {GREEN}✓{RESET} {msg}")
def err(msg):   print(f"  {RED}✗{RESET} {msg}")
def warn(msg):  print(f"  {YELLOW}⚠{RESET} {msg}")
def info(msg):  print(f"  {BLUE}ℹ{RESET} {msg}")
def hdr(title): print(f"\n{BOLD}{BLUE}{'─'*60}\n  {title}\n{'─'*60}{RESET}")

def ask(prompt, default=None):
    display = f"{prompt} [{default}]: " if default else f"{prompt}: "
    val = input(display).strip()
    return val if val else default


# ── AWS setup ─────────────────────────────────────────────────────────────────

def make_session(region: str) -> boto3.Session:
    """Create a boto3 session using the ambient credentials (CloudShell role)."""
    return boto3.Session(region_name=region)


def get_account_id(session: boto3.Session) -> str:
    return session.client('sts').get_caller_identity()['Account']


# ── Data source helpers ───────────────────────────────────────────────────────

def list_snowflake_datasources(qs, account_id: str):
    """Return all QuickSight data sources of type SNOWFLAKE."""
    sources = []
    kwargs  = {'AwsAccountId': account_id}
    while True:
        resp = qs.list_data_sources(**kwargs)
        for ds in resp.get('DataSources', []):
            if ds.get('Type') == 'SNOWFLAKE':
                sources.append(ds)
        next_token = resp.get('NextToken')
        if not next_token:
            break
        kwargs['NextToken'] = next_token
    return sources


def _create_datasource(qs, account_id: str, region: str) -> str:
    """Prompt for credentials and create a new QuickSight Snowflake data source."""
    print()
    ds_id   = ask("  Data source ID",   "movies-snowflake-datasource")
    ds_name = ask("  Data source name", "Movies Snowflake Data Source")
    secret  = ask("  Secrets Manager secret name", "snowflake-credentials")

    # Retrieve credentials from Secrets Manager
    sm = boto3.client('secretsmanager', region_name=region)
    try:
        resp   = sm.get_secret_value(SecretId=secret)
        creds  = json.loads(resp['SecretString'])
    except sm.exceptions.ResourceNotFoundException:
        err(f"Secret '{secret}' not found in Secrets Manager.")
        err("Run create_secret.py first, then re-run this script.")
        sys.exit(1)
    except Exception as e:
        err(f"Could not read secret: {e}")
        sys.exit(1)

    required = ['account', 'database', 'warehouse', 'user', 'password']
    missing  = [k for k in required if k not in creds]
    if missing:
        err(f"Secret is missing required keys: {', '.join(missing)}")
        sys.exit(1)

    host = f"{creds['account']}.snowflakecomputing.com"
    info(f"Creating data source: {ds_name}  ({host} / {creds['database']})")

    # Delete if already exists
    try:
        qs.delete_data_source(AwsAccountId=account_id, DataSourceId=ds_id)
        ok("Deleted existing data source with same ID")
        time.sleep(3)
    except qs.exceptions.ResourceNotFoundException:
        pass

    response = qs.create_data_source(
        AwsAccountId=account_id,
        DataSourceId=ds_id,
        Name=ds_name,
        Type='SNOWFLAKE',
        DataSourceParameters={
            'SnowflakeParameters': {
                'Host':      host,
                'Database':  creds['database'],
                'Warehouse': creds['warehouse'],
            }
        },
        Credentials={
            'CredentialPair': {
                'Username': creds['user'],
                'Password': creds['password'],
            }
        },
    )
    ok(f"Data source created: {response['DataSourceId']}")
    ok(f"ARN: {response['Arn']}")
    return response['Arn']


def select_or_create_datasource(qs, account_id: str, region: str) -> str:
    """List existing Snowflake data sources and let the user pick one or create new."""
    hdr("QuickSight Data Source")
    sources = list_snowflake_datasources(qs, account_id)

    if sources:
        print()
        for i, ds in enumerate(sources, start=1):
            params = ds.get('DataSourceParameters', {}).get('SnowflakeParameters', {})
            host   = params.get('Host', '?')
            db     = params.get('Database', '?')
            status = ds.get('Status', 'UNKNOWN')
            print(f"  [{i}] {ds['Name']}")
            print(f"      ID: {ds['DataSourceId']}  |  {host} / {db}  |  {status}")
    else:
        print()
        warn("No Snowflake data sources found in this account/region.")

    print(f"\n  [N] Create a new data source")
    print(f"  [Q] Quit")
    print()

    while True:
        choice = ask("Select").strip().upper()
        if choice == 'Q':
            sys.exit(0)
        if choice == 'N':
            return _create_datasource(qs, account_id, region)
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(sources):
                ds  = sources[idx]
                arn = ds['Arn']
                ok(f"Using: {ds['Name']}  ({ds['DataSourceId']})")
                return arn
        except (ValueError, TypeError):
            pass
        warn("Invalid choice — try again.")


# ── Schema generation ─────────────────────────────────────────────────────────

def generate_schema(datasource_arn: str, csv_path: str, database: str,
                    dataset_id: str, dataset_name: str, output: str) -> dict:
    """Parse the DDL CSV and produce a QuickSight dataset schema dict."""
    hdr("Generate Dataset Schema")
    info(f"Parsing Snowflake DDL from: {csv_path}")

    parser = SnowflakeDDLParser()
    parser.load_from_csv(csv_path)
    parsed = parser.parse_all()

    ok(f"Found {len(parsed['tables'])} tables")
    ok(f"Found {len(parsed['relationships'])} relationships")
    ok(f"Found {len(parsed['dimensions'])} dimensions")
    ok(f"Found {len(parsed['facts'])} facts")
    ok(f"Found {len(parsed['metrics'])} metrics")

    info("Generating complete QuickSight dataset schema...")
    gen    = QuickSightSchemaGenerator(parsed)
    schema = gen.generate_complete_schema(
        datasource_arn=datasource_arn,
        database=database,
        dataset_id=dataset_id,
        dataset_name=dataset_name,
    )

    with open(output, 'w') as f:
        json.dump(schema, f, indent=2)
    ok(f"Schema saved to: {output}")
    return schema


# ── Dataset creation ──────────────────────────────────────────────────────────

def create_dataset(qs, account_id: str, schema: dict) -> str:
    """Delete any existing dataset and create a fresh one. Returns the ingestion ID."""
    hdr("Create QuickSight Dataset")
    dataset_id = schema['DataSetId']

    # Delete if exists
    try:
        qs.delete_data_set(AwsAccountId=account_id, DataSetId=dataset_id)
        ok(f"Deleted existing dataset: {dataset_id}")
        time.sleep(5)
    except qs.exceptions.ResourceNotFoundException:
        info(f"No existing dataset found: {dataset_id}")
    except Exception as e:
        warn(f"Could not delete existing dataset: {e}")

    response = qs.create_data_set(AwsAccountId=account_id, **schema)
    ok(f"Dataset created: {response['DataSetId']}")
    ok(f"Status: {response['Status']}")

    # Start SPICE ingestion
    ingestion_id = f"ingestion-{int(time.time())}"
    ing = qs.create_ingestion(
        AwsAccountId=account_id,
        DataSetId=dataset_id,
        IngestionId=ingestion_id,
        IngestionType='FULL_REFRESH',
    )
    ok(f"Ingestion started: {ing['IngestionId']}")
    return ingestion_id


# ── Ingestion monitor ─────────────────────────────────────────────────────────

def monitor_ingestion(qs, account_id: str, dataset_id: str, ingestion_id: str):
    """Poll ingestion status and print progress until complete or failed."""
    hdr("SPICE Ingestion")
    info(f"Monitoring ingestion: {ingestion_id}")
    info("(Ctrl+C to stop monitoring — ingestion will continue in the background)")
    print()

    terminal = {'COMPLETED', 'FAILED', 'CANCELLED'}
    dots     = 0
    try:
        while True:
            resp = qs.describe_ingestion(
                AwsAccountId=account_id,
                DataSetId=dataset_id,
                IngestionId=ingestion_id,
            )
            status = resp['Ingestion']['IngestionStatus']
            rows   = resp['Ingestion'].get('RowInfo', {})

            if status in terminal:
                break

            dots = (dots % 3) + 1
            print(f"\r  {BLUE}●{RESET} {status}{'.' * dots}   ", end='', flush=True)
            time.sleep(8)
    except KeyboardInterrupt:
        print()
        warn("Stopped monitoring. Run to check status:")
        info(f"  aws quicksight describe-ingestion --aws-account-id {account_id} "
             f"--data-set-id {dataset_id} --ingestion-id {ingestion_id}")
        return

    print()
    if status == 'COMPLETED':
        ok(f"Ingestion COMPLETED")
        ok(f"Rows ingested: {rows.get('RowsIngested', '?'):,}")
        ok(f"Rows dropped:  {rows.get('RowsDropped', 0):,}")
    else:
        error_info = resp['Ingestion'].get('ErrorInfo', {})
        err(f"Ingestion {status}: {error_info}")


# ── Dataset sharing ───────────────────────────────────────────────────────────

def share_dataset(qs, account_id: str, dataset_id: str, region: str):
    """Prompt for a username and share the dataset with full permissions."""
    hdr("Share Dataset (optional)")

    # List existing users for reference
    try:
        users_resp = qs.list_users(AwsAccountId=account_id, Namespace='default')
        users      = users_resp.get('UserList', [])
        if users:
            print("  Available QuickSight users:")
            for u in users[:15]:
                print(f"    {u['UserName']}")
            if len(users) > 15:
                info(f"  ... and {len(users) - 15} more")
            print()
    except Exception:
        pass

    username = ask("  Share with (username, or press Enter to skip)").strip()
    if not username:
        info("Skipping — dataset not shared.")
        return

    principal_arn = f"arn:aws:quicksight:{region}:{account_id}:user/default/{username}"
    try:
        qs.update_data_set_permissions(
            AwsAccountId=account_id,
            DataSetId=dataset_id,
            GrantPermissions=[{
                'Principal': principal_arn,
                'Actions': [
                    'quicksight:UpdateDataSetPermissions',
                    'quicksight:DescribeDataSet',
                    'quicksight:DescribeDataSetPermissions',
                    'quicksight:PassDataSet',
                    'quicksight:DescribeIngestion',
                    'quicksight:ListIngestions',
                    'quicksight:UpdateDataSet',
                    'quicksight:DeleteDataSet',
                    'quicksight:CreateIngestion',
                    'quicksight:CancelIngestion',
                ],
            }],
        )
        ok(f"Dataset shared with: {username}")
    except qs.exceptions.ResourceNotFoundException:
        err(f"User not found: {username}")
        warn("Check the username above and run manually:")
        info(f"  python test_complete_schema.py --share-with \"{username}\"")
    except Exception as e:
        err(f"Could not share dataset: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description='Snowflake → QuickSight interactive workflow')
    p.add_argument('--region', default=None, help='AWS region (default: prompted)')
    args = p.parse_args()

    print(f"\n{BOLD}{BLUE}{'='*60}")
    print(f"  Snowflake → QuickSight Workflow")
    print(f"{'='*60}{RESET}")

    # ── Step 1: AWS setup ─────────────────────────────────────────────────────
    hdr("AWS Setup")
    region     = args.region or ask("AWS region", "us-east-1")
    session    = make_session(region)
    account_id = get_account_id(session)
    qs         = session.client('quicksight', region_name=region)
    ok(f"Account ID: {account_id}")
    ok(f"Region:     {region}")

    # ── Step 2: Data source ───────────────────────────────────────────────────
    datasource_arn = select_or_create_datasource(qs, account_id, region)

    # ── Step 3: Schema generation ─────────────────────────────────────────────
    hdr("Schema Configuration")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_csv = os.path.join(script_dir, 'SF_DDL.csv')

    csv_path    = ask("  Path to SF_DDL.csv",  default_csv)
    database    = ask("  Snowflake database",  "MOVIES")
    dataset_id  = ask("  QuickSight dataset ID",   "movie-analytics-dataset")
    dataset_name = ask("  QuickSight dataset name", "Movie Analytics Dataset")
    schema_file = ask("  Schema output file", "quicksight_schema_complete.json")
    print()

    schema = generate_schema(
        datasource_arn=datasource_arn,
        csv_path=csv_path,
        database=database,
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        output=schema_file,
    )

    # ── Step 4: Create dataset ────────────────────────────────────────────────
    ingestion_id = create_dataset(qs, account_id, schema)

    # ── Step 5: Monitor ingestion ─────────────────────────────────────────────
    monitor = ask("\nMonitor ingestion progress? [Y/n]", "Y").strip().upper()
    if monitor != 'N':
        monitor_ingestion(qs, account_id, dataset_id, ingestion_id)

    # ── Step 6: Share ─────────────────────────────────────────────────────────
    share_dataset(qs, account_id, dataset_id, region)

    # ── Done ──────────────────────────────────────────────────────────────────
    print(f"\n{BOLD}{GREEN}{'='*60}")
    print(f"  Workflow complete!")
    print(f"{'='*60}{RESET}")
    print(f"\n  Dataset: {dataset_name}")
    print(f"  ID:      {dataset_id}")
    print(f"  ARN:     arn:aws:quicksight:{region}:{account_id}:dataset/{dataset_id}")
    print()


if __name__ == '__main__':
    main()
