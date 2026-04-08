#!/usr/bin/env python3
"""
Snowflake to QuickSight — End-to-End Interactive CLI

Workflow:
  1. AWS credentials setup
  2. Snowflake credentials (manual or from Secrets Manager)
  3. Validate Snowflake connectivity
  4. List semantic views → user selects one (or use CSV fallback)
  5. Fetch semantic view DDL from Snowflake
  6. Parse DDL and display summary
  7. List QuickSight Snowflake data sources → user selects or creates new
  8. Configure dataset (ID, name) — SPICE by default
  9. Create/replace QuickSight dataset
 10. Trigger SPICE ingestion and monitor progress
 11. Share dataset with selected admins/authors

Usage:
    python snowflake_to_quicksight.py [--profile PROFILE] [--region REGION]
"""

import boto3
import json
import sys
import time
import getpass
import re
import argparse
from typing import Dict, List, Optional, Tuple

from schema_generator import SnowflakeDDLParser, QuickSightSchemaGenerator, snowflake_type_to_qs

# ── ANSI colours ──────────────────────────────────────────────────────────────
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


# ── AWS helpers ───────────────────────────────────────────────────────────────

def make_aws_session(profile: Optional[str]) -> boto3.Session:
    if profile:
        return boto3.Session(profile_name=profile)
    return boto3.Session()


def get_account_id(session: boto3.Session) -> str:
    return session.client('sts').get_caller_identity()['Account']


# ── Secrets Manager ───────────────────────────────────────────────────────────

def load_secret(session: boto3.Session, region: str, secret_name: str) -> Dict:
    client = session.client('secretsmanager', region_name=region)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except client.exceptions.ResourceNotFoundException:
        err(f"Secret '{secret_name}' not found.")
        sys.exit(1)
    except Exception as e:
        err(f"Could not read secret: {e}")
        sys.exit(1)


def save_secret(session: boto3.Session, region: str, secret_name: str, creds: Dict):
    client = session.client('secretsmanager', region_name=region)
    secret_string = json.dumps(creds)
    try:
        client.describe_secret(SecretId=secret_name)
        client.update_secret(SecretId=secret_name, SecretString=secret_string)
        ok(f"Secret updated: {secret_name}")
    except client.exceptions.ResourceNotFoundException:
        client.create_secret(
            Name=secret_name,
            Description='Snowflake credentials for QuickSight data source',
            SecretString=secret_string,
        )
        ok(f"Secret created: {secret_name}")


# ── Snowflake credentials ─────────────────────────────────────────────────────

def collect_snowflake_credentials(session: boto3.Session, region: str) -> Dict:
    """Prompt for Snowflake credentials; optionally load from Secrets Manager."""
    hdr("Snowflake Credentials")
    print("  [1] Enter credentials manually")
    print("  [2] Load from AWS Secrets Manager")
    choice = ask("Select", "1")

    if choice == '2':
        secret_name = ask("Secret name", "snowflake-credentials")
        creds = load_secret(session, region, secret_name)
        required = ['account', 'user', 'password', 'warehouse', 'database']
        missing = [k for k in required if k not in creds]
        if missing:
            err(f"Secret is missing required fields: {', '.join(missing)}")
            sys.exit(1)
        ok(f"Credentials loaded from secret '{secret_name}'")
        ok(f"Account:   {creds['account']}")
        ok(f"User:      {creds['user']}")
        ok(f"Database:  {creds.get('database', '(not set)')}")
        ok(f"Warehouse: {creds.get('warehouse', '(not set)')}")
        return creds

    # Manual entry
    creds = {
        'account':   ask("Snowflake account (e.g. abc12345.us-east-1)"),
        'user':      ask("Snowflake user"),
        'password':  getpass.getpass("  Snowflake password: "),
        'warehouse': ask("Warehouse", "WORKSHOPWH"),
        'database':  ask("Database",  "MOVIES"),
    }
    if not creds['account'] or not creds['user'] or not creds['password']:
        err("Account, user, and password are required.")
        sys.exit(1)

    save_choice = ask("Save to AWS Secrets Manager? (y/N)", "N").lower()
    if save_choice == 'y':
        secret_name = ask("Secret name", "snowflake-credentials")
        save_secret(session, region, secret_name, creds)

    return creds


# ── Snowflake connectivity ────────────────────────────────────────────────────

def _sf_connect(creds: Dict):
    """Open a Snowflake connection and return the connector object."""
    try:
        import snowflake.connector
    except ImportError:
        err("snowflake-connector-python is not installed.")
        info("Run: pip install snowflake-connector-python")
        sys.exit(1)

    return snowflake.connector.connect(
        account=creds['account'],
        user=creds['user'],
        password=creds['password'],
        warehouse=creds.get('warehouse'),
        database=creds.get('database'),
    )


def validate_snowflake_connection(creds: Dict) -> bool:
    hdr("Validate Snowflake Connectivity")
    try:
        conn = _sf_connect(creds)
        cur = conn.cursor()
        cur.execute("SELECT CURRENT_USER(), CURRENT_ACCOUNT(), CURRENT_DATABASE(), CURRENT_WAREHOUSE()")
        row = cur.fetchone()
        cur.close()
        conn.close()
        ok(f"User:      {row[0]}")
        ok(f"Account:   {row[1]}")
        ok(f"Database:  {row[2]}")
        ok(f"Warehouse: {row[3]}")
        return True
    except Exception as e:
        err(f"Connection failed: {e}")
        return False


def list_semantic_views(creds: Dict, database: Optional[str] = None) -> List[Dict]:
    """Return list of semantic view dicts from Snowflake."""
    conn = _sf_connect(creds)
    cur = conn.cursor()
    try:
        if database:
            cur.execute(f"SHOW SEMANTIC VIEWS IN DATABASE {database}")
        else:
            cur.execute("SHOW SEMANTIC VIEWS")
        cols = [d[0].lower() for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception as e:
        warn(f"Could not list semantic views: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def fetch_column_types(creds: Dict, tables: List[Dict]) -> Dict[str, Dict[str, str]]:
    """
    Query INFORMATION_SCHEMA.COLUMNS for each table and return actual Snowflake types
    as QuickSight type strings.

    Returns:
        {TABLE_ALIAS_UPPER: {COL_NAME_UPPER: qs_type}}
    """
    conn = _sf_connect(creds)
    cur  = conn.cursor()
    result: Dict[str, Dict[str, str]] = {}
    try:
        for table in tables:
            db     = table.get('database') or creds.get('database', '')
            schema = table.get('schema', 'PUBLIC')
            tname  = table['table_name']
            alias  = table['alias'].upper()

            try:
                cur.execute(f"""
                    SELECT COLUMN_NAME, DATA_TYPE, NUMERIC_SCALE
                    FROM {db}.INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{tname}'
                """)
                rows = cur.fetchall()
                result[alias] = {
                    row[0].upper(): snowflake_type_to_qs(row[1], row[2])
                    for row in rows
                }
            except Exception as e:
                warn(f"Could not fetch types for {tname}: {e}")
    finally:
        cur.close()
        conn.close()
    return result


def fetch_semantic_view_ddl(creds: Dict, database: str, schema: str, view_name: str) -> str:
    """Fetch DDL for a semantic view using GET_DDL."""
    conn = _sf_connect(creds)
    cur = conn.cursor()
    try:
        sql = f"SELECT TO_VARCHAR(GET_DDL('SEMANTIC_VIEW', '{database}.{schema}.{view_name}'))"
        cur.execute(sql)
        row = cur.fetchone()
        return row[0] if row else ''
    finally:
        cur.close()
        conn.close()


def select_semantic_view(creds: Dict, database: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Interactively select a semantic view.
    Returns (database, schema, view_name) or (None, None, None) if using CSV.
    """
    hdr("Select Semantic View")
    views = list_semantic_views(creds, database)

    if views:
        print()
        for i, v in enumerate(views):
            name = v.get('name', v.get('Name', '?'))
            db   = v.get('database_name', v.get('database', database))
            sch  = v.get('schema_name',   v.get('schema', 'PUBLIC'))
            print(f"  [{i + 1}] {name}  ({db}.{sch})")
    else:
        warn("No semantic views found — you can enter a name manually or use CSV.")

    print(f"  [M] Enter view name manually")
    print(f"  [F] Use local CSV file as DDL source")
    print()

    while True:
        choice = ask("Select").strip().upper()
        if choice == 'F':
            return None, None, None
        if choice == 'M':
            db   = ask("Database",  database)
            sch  = ask("Schema",    "PUBLIC")
            name = ask("Semantic view name")
            return db, sch, name
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(views):
                v    = views[idx]
                name = v.get('name', v.get('Name'))
                db   = v.get('database_name', v.get('database', database))
                sch  = v.get('schema_name',   v.get('schema', 'PUBLIC'))
                return db, sch, name
        except (ValueError, TypeError):
            pass
        warn("Invalid choice — try again.")


def get_ddl_from_csv() -> str:
    """Prompt for a CSV path and load DDL from it."""
    csv_path = ask("Path to DDL CSV file", "SF_DDL.csv")
    parser = SnowflakeDDLParser()
    parser.load_from_csv(csv_path)
    return parser.ddl_content


# ── QuickSight data sources ───────────────────────────────────────────────────

def list_snowflake_datasources(qs, account_id: str) -> List[Dict]:
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


def select_or_create_datasource(
    qs,
    account_id: str,
    creds: Dict,
    region: str,
    session: boto3.Session,
) -> str:
    """
    Show existing Snowflake data sources and let user pick one or create new.
    Returns the ARN of the selected/created data source.
    """
    hdr("QuickSight Data Source")
    sources = list_snowflake_datasources(qs, account_id)

    if sources:
        print()
        for i, ds in enumerate(sources):
            params  = ds.get('DataSourceParameters', {}).get('SnowflakeParameters', {})
            host    = params.get('Host', '?')
            db      = params.get('Database', '?')
            status  = ds.get('Status', 'UNKNOWN')
            print(f"  [{i + 1}] {ds['Name']}")
            print(f"        ID: {ds['DataSourceId']}  |  {host} / {db}  |  {status}")
    else:
        print("  (no Snowflake data sources found)")

    print(f"  [N] Create a new data source")
    print(f"  [Q] Quit")
    print()

    while True:
        choice = ask("Select").strip().upper()
        if choice == 'Q':
            sys.exit(0)
        if choice == 'N':
            return _create_snowflake_datasource(qs, account_id, creds, region)
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(sources):
                ds  = sources[idx]
                arn = ds['Arn']
                ok(f"Using data source: {ds['Name']}  ({ds['DataSourceId']})")
                return arn
        except (ValueError, TypeError):
            pass
        warn("Invalid choice — try again.")


def _create_snowflake_datasource(qs, account_id: str, creds: Dict, region: str) -> str:
    """Create a new QuickSight Snowflake data source and return its ARN."""
    print()
    ds_id   = ask("Data source ID",   "snowflake-datasource")
    ds_name = ask("Data source name", "Snowflake Data Source")

    # Delete if it already exists
    try:
        qs.delete_data_source(AwsAccountId=account_id, DataSourceId=ds_id)
        ok("Deleted existing data source with same ID")
        time.sleep(3)
    except qs.exceptions.ResourceNotFoundException:
        pass

    host = f"{creds['account']}.snowflakecomputing.com"
    info(f"Creating data source: {ds_name} → {host}")

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

    arn = response['Arn']
    ok(f"Data source created: {ds_id}")
    ok(f"ARN: {arn}")
    return arn


# ── Dataset creation ──────────────────────────────────────────────────────────

def create_or_replace_dataset(qs, account_id: str, schema: Dict) -> Dict:
    """Delete any existing dataset with the same ID, then create the new one."""
    dataset_id = schema['DataSetId']

    try:
        qs.delete_data_set(AwsAccountId=account_id, DataSetId=dataset_id)
        ok(f"Deleted existing dataset: {dataset_id}")
        time.sleep(5)
    except qs.exceptions.ResourceNotFoundException:
        pass

    info("Creating QuickSight dataset…")
    response = qs.create_data_set(AwsAccountId=account_id, **schema)
    ok(f"Dataset created: {response['DataSetId']}")
    ok(f"Status: {response['Status']}")
    return response


# ── SPICE ingestion ───────────────────────────────────────────────────────────

def trigger_ingestion(qs, account_id: str, dataset_id: str) -> str:
    """Start a FULL_REFRESH SPICE ingestion and return the ingestion ID."""
    ingestion_id = f"ingestion-{int(time.time())}"
    qs.create_ingestion(
        AwsAccountId=account_id,
        DataSetId=dataset_id,
        IngestionId=ingestion_id,
        IngestionType='FULL_REFRESH',
    )
    ok(f"Ingestion started: {ingestion_id}")
    return ingestion_id


def monitor_ingestion(qs, account_id: str, dataset_id: str, ingestion_id: str):
    """Poll until ingestion completes, fails, or times out (5 minutes)."""
    info("Waiting for SPICE ingestion to complete…")
    max_checks = 30
    for attempt in range(1, max_checks + 1):
        time.sleep(10)
        try:
            resp   = qs.describe_ingestion(
                AwsAccountId=account_id,
                DataSetId=dataset_id,
                IngestionId=ingestion_id,
            )
            status = resp['Ingestion']['IngestionStatus']
            if status == 'COMPLETED':
                rows = resp['Ingestion'].get('RowInfo', {}).get('RowsIngested', '?')
                ok(f"Ingestion completed — rows ingested: {rows}")
                return
            if status == 'FAILED':
                error_info = resp['Ingestion'].get('ErrorInfo', {})
                err(f"Ingestion failed: {error_info.get('Message', 'unknown error')}")
                return
            print(f"    {status} (check {attempt}/{max_checks})…", end='\r', flush=True)
        except Exception as e:
            warn(f"Could not check ingestion status: {e}")
            return
    warn("Ingestion verification timed out. Check the QuickSight console.")


# ── User sharing ──────────────────────────────────────────────────────────────

_DATASET_ACTIONS = [
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
]


_SHAREABLE_ROLES = {'ADMIN', 'AUTHOR', 'ADMIN_PRO', 'AUTHOR_PRO'}


def list_qs_users(qs, account_id: str) -> List[Dict]:
    """Return all QuickSight users with a shareable role (paginated)."""
    users  = []
    kwargs = {'AwsAccountId': account_id, 'Namespace': 'default'}
    while True:
        resp = qs.list_users(**kwargs)
        for u in resp.get('UserList', []):
            role = u.get('Role', '')
            arn  = u.get('Arn', '')
            # Include only users with valid ARNs and shareable roles
            if role in _SHAREABLE_ROLES and arn.startswith('arn:'):
                users.append(u)
        next_token = resp.get('NextToken')
        if not next_token:
            break
        kwargs['NextToken'] = next_token
    return users


def _lookup_user_by_name(qs, account_id: str, username: str) -> Optional[Dict]:
    """Fetch a single QuickSight user by UserName (tries default namespace)."""
    try:
        resp = qs.describe_user(
            AwsAccountId=account_id,
            Namespace='default',
            UserName=username,
        )
        return resp['User']
    except Exception:
        return None


def select_users_to_share(qs, account_id: str) -> List[Dict]:
    """
    Ask whether to list available users or enter a username directly.
    Validates role and ARN before returning.
    Returns a list of user dicts to share with.
    """
    hdr("Share Dataset")
    print()
    print("  [1] List available users (ADMIN / AUTHOR / ADMIN_PRO / AUTHOR_PRO)")
    print("  [2] Enter username directly")
    print("  [S] Skip sharing")
    print()

    while True:
        choice = ask("Select", "S").strip().upper()

        # ── Skip ──────────────────────────────────────────────────────────────
        if choice == 'S':
            return []

        # ── List users ────────────────────────────────────────────────────────
        if choice == '1':
            info("Fetching QuickSight users…")
            users = list_qs_users(qs, account_id)
            if not users:
                warn("No shareable users found (ADMIN / AUTHOR / ADMIN_PRO / AUTHOR_PRO).")
                continue

            print()
            for i, u in enumerate(users):
                role  = u.get('Role', '?')
                email = u.get('Email', '')
                email_str = f"  {email}" if email else ''
                print(f"  [{i + 1}] {u['UserName']}  (Role: {role}{email_str})")
            print()
            print("  Enter numbers to share with (comma-separated), or 'B' to go back:")

            while True:
                raw = ask("Selection").strip().upper()
                if raw == 'B':
                    break
                try:
                    indices  = [int(x.strip()) - 1 for x in raw.split(',') if x.strip()]
                    selected = [users[i] for i in indices if 0 <= i < len(users)]
                    if selected:
                        return selected
                    warn("No valid selections — try again or type 'B' to go back.")
                except (ValueError, IndexError):
                    warn("Invalid input — use numbers like: 1,3 or type 'B'.")
            continue  # back to outer menu

        # ── Manual username entry ─────────────────────────────────────────────
        if choice == '2':
            while True:
                username = ask("QuickSight username").strip()
                if not username:
                    warn("Username cannot be empty.")
                    continue

                info(f"Looking up user '{username}'…")
                user = _lookup_user_by_name(qs, account_id, username)
                if not user:
                    err(f"User '{username}' not found in the default namespace.")
                    retry = ask("Try another username? (Y/n)", "Y").strip().upper()
                    if retry == 'N':
                        break
                    continue

                role = user.get('Role', '')
                arn  = user.get('Arn', '')
                if role not in _SHAREABLE_ROLES:
                    err(f"User '{username}' has role '{role}' which is not shareable.")
                    info(f"Shareable roles: {', '.join(sorted(_SHAREABLE_ROLES))}")
                    retry = ask("Try another username? (Y/n)", "Y").strip().upper()
                    if retry == 'N':
                        break
                    continue

                if not arn.startswith('arn:'):
                    err(f"User '{username}' has an invalid ARN: {arn}")
                    break

                ok(f"Found: {username}  Role: {role}  Email: {user.get('Email', 'N/A')}")
                add_more = ask("Add another user? (y/N)", "N").strip().upper()
                selected = [user]
                while add_more == 'Y':
                    extra_name = ask("QuickSight username").strip()
                    if not extra_name:
                        break
                    extra = _lookup_user_by_name(qs, account_id, extra_name)
                    if not extra:
                        err(f"User '{extra_name}' not found.")
                    elif extra.get('Role', '') not in _SHAREABLE_ROLES:
                        err(f"User '{extra_name}' has non-shareable role '{extra.get('Role')}'.")
                    elif not extra.get('Arn', '').startswith('arn:'):
                        err(f"User '{extra_name}' has invalid ARN.")
                    else:
                        ok(f"Added: {extra_name}  Role: {extra.get('Role')}")
                        selected.append(extra)
                    add_more = ask("Add another user? (y/N)", "N").strip().upper()
                return selected

            continue  # back to outer menu

        warn("Invalid choice — enter 1, 2, or S.")


def share_dataset(qs, account_id: str, dataset_id: str, users: List[Dict], region: str):
    """Grant full dataset permissions to each selected user."""
    for u in users:
        user_arn = u.get('Arn', '')
        if not user_arn or 'N/A' in user_arn or not user_arn.startswith('arn:'):
            warn(f"Skipping {u['UserName']} — invalid ARN: {user_arn}")
            continue
        try:
            qs.update_data_set_permissions(
                AwsAccountId=account_id,
                DataSetId=dataset_id,
                GrantPermissions=[{'Principal': user_arn, 'Actions': _DATASET_ACTIONS}],
            )
            ok(f"Shared with: {u['UserName']} ({u.get('Role', '?')})")
        except Exception as e:
            err(f"Failed to share with {u['UserName']}: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def print_banner():
    print(f"""
{BOLD}{BLUE}╔══════════════════════════════════════════════════════════════╗
║      Snowflake  →  Amazon QuickSight  |  End-to-End Setup    ║
╚══════════════════════════════════════════════════════════════╝{RESET}
""")


def main():
    arg_parser = argparse.ArgumentParser(
        description='Snowflake to QuickSight end-to-end interactive CLI'
    )
    arg_parser.add_argument('--profile', help='AWS profile name (optional)')
    arg_parser.add_argument('--region',  default='us-east-1', help='AWS region (default: us-east-1)')
    args = arg_parser.parse_args()

    print_banner()

    # ── AWS setup ─────────────────────────────────────────────────────────────
    hdr("AWS Setup")
    profile = args.profile or ask("AWS profile (leave empty for default)") or None
    region  = args.region

    try:
        session    = make_aws_session(profile)
        account_id = get_account_id(session)
        ok(f"Account ID: {account_id}")
        ok(f"Region:     {region}")
    except Exception as e:
        err(f"AWS credentials error: {e}")
        sys.exit(1)

    qs = session.client('quicksight', region_name=region)

    # ── Snowflake credentials ─────────────────────────────────────────────────
    creds = collect_snowflake_credentials(session, region)

    # ── Validate Snowflake connection ─────────────────────────────────────────
    if not validate_snowflake_connection(creds):
        err("Cannot continue without a valid Snowflake connection.")
        sys.exit(1)

    # ── Select semantic view ──────────────────────────────────────────────────
    sf_database, sf_schema, sf_view = select_semantic_view(creds, creds.get('database', 'MOVIES'))

    # ── Fetch / load DDL ──────────────────────────────────────────────────────
    hdr("Fetch Semantic View DDL")
    if sf_view is None:
        ddl_text = get_ddl_from_csv()
        ok("DDL loaded from CSV")
    else:
        info(f"Fetching DDL for: {sf_database}.{sf_schema}.{sf_view}")
        try:
            ddl_text = fetch_semantic_view_ddl(creds, sf_database, sf_schema, sf_view)
            if not ddl_text:
                err("GET_DDL returned empty content.")
                sys.exit(1)
            ok(f"DDL fetched ({len(ddl_text)} characters)")
        except Exception as e:
            err(f"Failed to fetch DDL: {e}")
            sys.exit(1)

    # ── Parse DDL ─────────────────────────────────────────────────────────────
    hdr("Parse Semantic View DDL")
    try:
        ddl_parser = SnowflakeDDLParser()
        ddl_parser.load_from_string(ddl_text)
        parsed = ddl_parser.parse_all()
    except Exception as e:
        err(f"Failed to parse DDL: {e}")
        sys.exit(1)

    ok(f"Tables:        {len(parsed['tables'])}")
    ok(f"Relationships: {len(parsed['relationships'])}")
    ok(f"Dimensions:    {len(parsed['dimensions'])}")
    ok(f"Facts:         {len(parsed['facts'])}")
    ok(f"Metrics:       {len(parsed['metrics'])}")

    # ── Select or create QuickSight data source ───────────────────────────────
    datasource_arn = select_or_create_datasource(qs, account_id, creds, region, session)

    # ── Dataset configuration ─────────────────────────────────────────────────
    hdr("Dataset Configuration")
    dataset_id   = ask("Dataset ID",   "movie-analytics-dataset")
    dataset_name = ask("Dataset name", "Movie Analytics Dataset")
    ok("Import mode: SPICE (default)")

    # ── Generate schema ───────────────────────────────────────────────────────
    hdr("Generate QuickSight Schema")
    try:
        # Fetch actual Snowflake column types when connected live (improves type accuracy)
        col_type_overrides: Optional[Dict] = None
        if sf_view is not None:  # skip when DDL was loaded from local CSV
            try:
                col_type_overrides = fetch_column_types(creds, parsed['tables'])
                ok(f"Fetched actual column types from Snowflake for {len(col_type_overrides)} tables")
            except Exception as e:
                warn(f"Could not fetch column types (using inferred types): {e}")

        generator = QuickSightSchemaGenerator(parsed)
        schema    = generator.generate_complete_schema(
            datasource_arn=datasource_arn,
            database=creds.get('database', 'MOVIES'),
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            column_type_overrides=col_type_overrides,
        )
    except Exception as e:
        err(f"Schema generation failed: {e}")
        sys.exit(1)

    schema_path = f"{dataset_id}_schema.json"
    with open(schema_path, 'w') as fh:
        json.dump(schema, fh, indent=2)
    ok(f"Schema saved to: {schema_path}")
    ok(f"Physical tables: {len(schema['PhysicalTableMap'])}")
    ok(f"Logical tables:  {len(schema['LogicalTableMap'])}")

    # ── Create dataset ────────────────────────────────────────────────────────
    hdr("Create QuickSight Dataset")
    try:
        create_or_replace_dataset(qs, account_id, schema)
    except Exception as e:
        err(f"Dataset creation failed: {e}")
        sys.exit(1)

    # ── Trigger SPICE ingestion ───────────────────────────────────────────────
    hdr("SPICE Ingestion")
    ingestion_id = trigger_ingestion(qs, account_id, dataset_id)
    monitor_ingestion(qs, account_id, dataset_id, ingestion_id)

    # ── Share dataset ─────────────────────────────────────────────────────────
    selected_users = select_users_to_share(qs, account_id)
    if selected_users:
        share_dataset(qs, account_id, dataset_id, selected_users, region)
    else:
        info("Skipped sharing.")

    # ── Summary ───────────────────────────────────────────────────────────────
    hdr("Done")
    ok(f"Dataset ID:   {dataset_id}")
    ok(f"Dataset name: {dataset_name}")
    ok(f"Schema file:  {schema_path}")
    if selected_users:
        ok(f"Shared with:  {', '.join(u['UserName'] for u in selected_users)}")
    print(f"\n  {BLUE}Open QuickSight → Datasets to start building analyses.{RESET}\n")


if __name__ == '__main__':
    main()
