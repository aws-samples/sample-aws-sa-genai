# Snowflake to QuickSight — Solution Package

Create an Amazon QuickSight SPICE dataset from a Snowflake Semantic View entirely from the AWS CloudShell. No direct connection to Snowflake is required — the Semantic View DDL is exported to a CSV file and uploaded to CloudShell.

---

## Quick Start

```bash
unzip Solution_Package.zip
cd Solution_Package
# upload SF_DDL.csv here
python run_workflow.py
```

`run_workflow.py` is the single entry point. It walks you through all six steps interactively — AWS setup, data source selection or creation, schema generation, dataset creation, ingestion monitoring, and sharing.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| AWS CloudShell access | Open from the AWS Console toolbar |
| Python 3 with `boto3` | Pre-installed in CloudShell |
| IAM permissions | Secrets Manager, QuickSight, STS |
| Snowflake DDL CSV | Export from Snowflake notebook (see Step 0) |
| QuickSight account | Subscribed in the same AWS account/region |

---

## Step 0 — Prepare the Environment

1. Open the **AWS Console** and click the **CloudShell** icon in the top toolbar.

2. Upload `Solution_Package.zip` using the **Actions → Upload file** menu in CloudShell.

3. Unzip and enter the directory:

```bash
unzip Solution_Package.zip
cd Solution_Package
```

4. Upload the `SF_DDL.csv` file you downloaded from the Snowflake notebook (the output of `GET_DDL` on the Semantic View).

---

## Step 1 — Create the AWS Secret

Store your Snowflake credentials in AWS Secrets Manager before running the workflow. The interactive workflow reads this secret when creating the QuickSight data source — your password never appears in plain text in any subsequent command.

```bash
python create_secret.py \
  --secret-name snowflake-credentials \
  --account YOUR_SNOWFLAKE_ACCOUNT \
  --database MOVIES \
  --warehouse WORKSHOPWH \
  --user YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --region us-east-1
```

**Expected output:**
```
Creating/updating secret: snowflake-credentials
...
✓ Secret created successfully!
  ARN: arn:aws:secretsmanager:us-east-1:...
```

The secret is stored as:
```json
{
  "account": "your-account.us-east-1",
  "database": "MOVIES",
  "warehouse": "WORKSHOPWH",
  "user": "your_username",
  "password": "your_password"
}
```

---

## Steps 2–6 — Run the Interactive Workflow

Once the secret is created, run the single interactive script:

```bash
python run_workflow.py
```

The script walks through five steps:

### Step 2 — Select or Create a QuickSight Data Source

The script lists all existing Snowflake data sources in your account:

```
────────────────────────────────────────────────────
  QuickSight Data Source
────────────────────────────────────────────────────

  [1] Movies Snowflake Data Source
      ID: movies-snowflake-datasource  |  abc12345.snowflakecomputing.com / MOVIES  |  CREATION_SUCCESSFUL

  [N] Create a new data source
  [Q] Quit

Select:
```

Choose an existing source by number, or `N` to create a new one. When creating, the script reads credentials from the Secrets Manager secret created in Step 1.

### Step 3 — Generate the QuickSight Schema

The script parses `SF_DDL.csv` and generates `quicksight_schema_complete.json`.

**Expected output:**
```
  ✓ Found 3 tables
  ✓ Found 2 relationships
  ✓ Found 17 dimensions
  ✓ Found 1 facts
  ✓ Found 7 metrics
  ✓ Schema saved to: quicksight_schema_complete.json
```

The schema includes **25 output columns**:

| Category | Columns |
|---|---|
| Movie | MOVIE_TITLE, RELEASE_YEAR, MOVIES_MOVIE_ID |
| User | USER_FIRST_NAME, USER_LAST_NAME, USER_FULL_NAME, USER_EMAIL, USER_CITY, USER_STATE, USER_COUNTRY, USERS_USER_ID |
| Rating | RATING_VALUE, RATING_TIMESTAMP, RATING_YEAR, RATING_MONTH, RATING_DAY, RATINGS_USER_ID, RATINGS_MOVIE_ID |
| Metrics | MOVIES_DISTINCT_MOVIES, USERS_DISTINCT_USERS, RATINGS_TOTAL_RATINGS, RATINGS_AVG_RATING, RATINGS_DISTINCT_USERS, RATINGS_DISTINCT_MOVIES, RATINGS_POPULARITY_SCORE |

### Step 4 — Create the Dataset

**Expected output:**
```
  ✓ Dataset created: movie-analytics-dataset
  ✓ Status: 201
  ✓ Ingestion started: ingestion-1769081615
```

### Step 5 — Monitor SPICE Ingestion

The script polls ingestion status and shows live progress. Press Ctrl+C to stop monitoring — ingestion continues in the background.

**Expected output when complete:**
```
  ✓ Ingestion COMPLETED
  ✓ Rows ingested: 378,436
  ✓ Rows dropped:  0
```

To check status manually:
```bash
aws quicksight describe-ingestion \
  --aws-account-id YOUR_ACCOUNT_ID \
  --data-set-id movie-analytics-dataset \
  --ingestion-id ingestion-1769081615 \
  --region us-east-1
```

### Step 6 — Share the Dataset (Optional)

The script lists available QuickSight users and prompts for a username. Press Enter to skip.

---

## Script Reference

| Script | Purpose |
|---|---|
| `run_workflow.py` | **Main entry point** — interactive end-to-end workflow |
| `create_secret.py` | Create/update Snowflake credentials in Secrets Manager |
| `create_snowflake_datasource.py` | Create a QuickSight data source (standalone) |
| `generate_quicksight_schema.py` | Parse DDL CSV → QuickSight schema JSON (standalone) |
| `test_complete_schema.py` | Create dataset + start ingestion + share (standalone) |
| `validate_setup.py` | Pre-flight check of AWS credentials and dependencies |
| `setup_secrets.sh` | Interactive shell script alternative for secret creation |
| `example_workflow.sh` | Manual step-by-step command reference |

---

## Troubleshooting

**Secret already exists**
`create_secret.py` updates the existing secret automatically. No action needed.

**Data source `CREATION_FAILED`**
Verify the Snowflake account identifier format (e.g. `abc12345.us-east-1`). QuickSight validates connectivity at creation time — the credentials must be correct even though no live query runs until SPICE ingestion.

**Schema generation: `No tables found`**
Check that `SF_DDL.csv` was exported correctly from Snowflake. The file must have a header row with the DDL in the second column.

**Dataset creation: `Field does not exist`**
A calculated field references a column that was dropped or renamed. Re-run `generate_quicksight_schema.py` (or restart `run_workflow.py`) to regenerate the schema from the current DDL.

**Ingestion `FAILED`**
Run `describe-ingestion` and check the `ErrorInfo` field. Common causes: Snowflake warehouse suspended, network policy blocking the QuickSight IP range, or incorrect credentials in the secret.
