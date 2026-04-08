#!/bin/bash
# Snowflake → QuickSight workflow
#
# RECOMMENDED: run the interactive script which handles all 6 steps,
# including listing / creating the QuickSight data source:
#
#   python run_workflow.py
#
# ─────────────────────────────────────────────────────────────────────────────
# MANUAL STEP-BY-STEP (if you prefer to run each script individually):
# ─────────────────────────────────────────────────────────────────────────────

# Step 1: Create AWS secret for Snowflake credentials
# python create_secret.py \
#   --secret-name snowflake-credentials \
#   --account YOUR_SNOWFLAKE_ACCOUNT \
#   --database MOVIES \
#   --warehouse WORKSHOPWH \
#   --user YOUR_USERNAME \
#   --password YOUR_PASSWORD \
#   --region us-east-1

# Step 2: Create QuickSight data source
# python create_snowflake_datasource.py \
#   --datasource-id movies-snowflake-datasource \
#   --datasource-name "Movies Snowflake Data Source" \
#   --secret-name snowflake-credentials \
#   --region us-east-1

# Step 3: Generate QuickSight schema from Snowflake DDL CSV
# python generate_quicksight_schema.py \
#   --csv-path SF_DDL.csv \
#   --datasource-arn "arn:aws:quicksight:us-east-1:YOUR_ACCOUNT_ID:datasource/movies-snowflake-datasource" \
#   --database MOVIES \
#   --output quicksight_schema_complete.json

# Step 4: Create dataset and start SPICE ingestion
# python test_complete_schema.py \
#   --region us-east-1 \
#   --share-with "Administrator/YOUR_USERNAME"

# Step 5: Check ingestion status
# aws quicksight describe-ingestion \
#   --aws-account-id YOUR_ACCOUNT_ID \
#   --data-set-id movie-analytics-dataset \
#   --ingestion-id INGESTION_ID \
#   --region us-east-1
