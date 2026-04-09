# Snowflake → Amazon QuickSight — End-to-End Setup

Connects to a Snowflake Semantic View, converts its definition into an Amazon QuickSight SPICE dataset, and shares it with your team — all from a single interactive CLI.

## Files

| File | Purpose |
|------|---------|
| `snowflake_to_quicksight.py` | Main interactive CLI — run this |
| `schema_generator.py` | DDL parser + QuickSight schema builder (used internally; also works standalone) |
| `SF_DDL.csv` | Sample Snowflake Semantic View DDL (CSV fallback when not connecting live) |
| `config.env.example` | Environment variable reference |
| `requirements.txt` | Python dependencies |

## Prerequisites

- Python 3.8+
- AWS credentials configured (`aws configure` or an IAM role)
- QuickSight account in your AWS account
- Snowflake account with at least one Semantic View

## Installation

```bash
pip install -r requirements.txt
```

## How to Run

```bash
python snowflake_to_quicksight.py [--profile PROFILE] [--region REGION]
```

**Options**

| Flag | Default | Description |
|------|---------|-------------|
| `--profile` | (default credentials) | AWS named profile |
| `--region` | `us-east-1` | AWS region where QuickSight is deployed |

**Examples**

```bash
# Using default AWS credentials
python snowflake_to_quicksight.py

# Using a named profile in a specific region
python snowflake_to_quicksight.py --profile myprofile --region us-west-2
```

## Interactive Workflow

### Step 1 — AWS Setup
Validates your AWS credentials and displays the account ID and region.

### Step 2 — Snowflake Credentials
Choose how to supply Snowflake credentials:

- **[1] Enter manually** — prompted for account, user, password, warehouse, and database. You will be offered the option to save them to AWS Secrets Manager for future runs.
- **[2] Load from Secrets Manager** — provide a secret name; the secret must contain the keys `account`, `user`, `password`, `warehouse`, and `database`.

### Step 3 — Validate Snowflake Connectivity
Opens a test connection to Snowflake and prints the current user, account, database, and warehouse. The workflow stops here if the connection fails.

### Step 4 — Select Semantic View
Lists all Semantic Views visible in your Snowflake database. Choose one, or:

- **[M]** Enter a database, schema, and view name manually.
- **[F]** Skip live connection and load DDL from a local CSV file (useful for testing).

### Step 5 — Fetch Semantic View DDL
Runs `GET_DDL('SEMANTIC_VIEW', '<db>.<schema>.<view>')` on Snowflake and retrieves the full DDL as a string.

### Step 6 — Parse DDL
Parses the DDL and prints a summary:

```
  ✓ Tables:        3
  ✓ Relationships: 2
  ✓ Dimensions:    14
  ✓ Facts:         1
  ✓ Metrics:       7
```

### Step 7 — QuickSight Data Source
Lists existing Snowflake data sources in QuickSight. Choose one or create a new one:

- Selecting an existing source reuses it as-is.
- Creating a new source prompts for an ID and display name, then provisions it using your Snowflake credentials.

### Step 8 — Dataset Configuration
Choose how to apply the dataset:

- **[1] Create new dataset** — enter a new dataset ID and display name. If a dataset with the same ID already exists it will be deleted and recreated. Import mode is always **SPICE**.
- **[2] Update existing dataset** — update an existing dataset in place (no delete/recreate). Two ways to identify it:
  - **[A] Pick from list** — lists only datasets that use the Snowflake data source selected in Step 7. Type a search term at any time to filter the list by name or ID; type a number to select.
  - **[B] Type dataset ID** — enter the dataset ID directly if you already know it.

### Step 9 — Create or Update QuickSight Dataset
Generates the full QuickSight dataset schema (physical tables, joins, column renames, type casts, calculated fields, and column descriptions) and either creates or updates the dataset depending on the choice made in Step 8. The schema is also saved locally as `<dataset-id>_schema.json` for reference.

### Step 10 — SPICE Ingestion
Triggers a `FULL_REFRESH` ingestion and polls every 10 seconds until it completes (up to 5 minutes). On completion, the number of ingested rows is displayed.

### Step 11 — Share Dataset
Lists all QuickSight users with the **ADMIN** or **AUTHOR** role. Enter the numbers of the users you want to share with as a comma-separated list, or type `skip`.

```
  [1] alice  (Role: ADMIN   Email: alice@example.com)
  [2] bob    (Role: AUTHOR  Email: bob@example.com)
  [3] carol  (Role: AUTHOR  Email: carol@example.com)

  Selection: 1,3
```

Each selected user receives full dataset permissions (describe, update, delete, ingest, and share).

## Standalone Schema Generator

`schema_generator.py` can be used on its own to generate a QuickSight schema JSON from a local CSV file:

```bash
python schema_generator.py \
  --csv-path SF_DDL.csv \
  --datasource-arn arn:aws:quicksight:us-east-1:123456789012:datasource/my-ds \
  --database MOVIES \
  --dataset-id my-dataset \
  --dataset-name "My Dataset" \
  --output schema.json
```

## AWS Permissions Required

The IAM identity running this tool needs the following permissions:

**Secrets Manager** (only if using credential storage)
- `secretsmanager:GetSecretValue`
- `secretsmanager:CreateSecret`
- `secretsmanager:UpdateSecret`
- `secretsmanager:DescribeSecret`

**QuickSight**
- `quicksight:ListDataSources`
- `quicksight:CreateDataSource`
- `quicksight:DeleteDataSource`
- `quicksight:CreateDataSet`
- `quicksight:DeleteDataSet`
- `quicksight:CreateIngestion`
- `quicksight:DescribeIngestion`
- `quicksight:ListUsers`
- `quicksight:UpdateDataSetPermissions`

**STS**
- `sts:GetCallerIdentity`
