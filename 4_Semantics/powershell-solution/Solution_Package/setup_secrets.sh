#!/bin/bash
# Helper script to create AWS Secrets Manager secret for Snowflake credentials

echo "AWS Secrets Manager - Snowflake Credentials Setup"
echo "=================================================="
echo ""

# Prompt for values
read -p "Enter Snowflake account identifier: " SF_ACCOUNT
read -p "Enter Snowflake database name [MOVIES]: " SF_DATABASE
SF_DATABASE=${SF_DATABASE:-MOVIES}
read -p "Enter Snowflake warehouse name [WORKSHOPWH]: " SF_WAREHOUSE
SF_WAREHOUSE=${SF_WAREHOUSE:-WORKSHOPWH}
read -p "Enter Snowflake username: " SF_USER
read -sp "Enter Snowflake password: " SF_PASSWORD
echo ""
read -p "Enter AWS region [us-east-1]: " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}
read -p "Enter secret name [snowflake-credentials]: " SECRET_NAME
SECRET_NAME=${SECRET_NAME:-snowflake-credentials}

# Create JSON secret
SECRET_JSON=$(cat <<EOF
{
  "account": "$SF_ACCOUNT",
  "database": "$SF_DATABASE",
  "warehouse": "$SF_WAREHOUSE",
  "user": "$SF_USER",
  "password": "$SF_PASSWORD"
}
EOF
)

echo ""
echo "Creating secret in AWS Secrets Manager..."

# Check if secret already exists
if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region "$AWS_REGION" &>/dev/null; then
    echo "Secret '$SECRET_NAME' already exists. Updating..."
    aws secretsmanager update-secret \
        --secret-id "$SECRET_NAME" \
        --secret-string "$SECRET_JSON" \
        --region "$AWS_REGION"
    
    if [ $? -eq 0 ]; then
        echo "✓ Secret updated successfully!"
    else
        echo "✗ Failed to update secret"
        exit 1
    fi
else
    echo "Creating new secret..."
    aws secretsmanager create-secret \
        --name "$SECRET_NAME" \
        --description "Snowflake credentials for QuickSight data source" \
        --secret-string "$SECRET_JSON" \
        --region "$AWS_REGION"
    
    if [ $? -eq 0 ]; then
        echo "✓ Secret created successfully!"
    else
        echo "✗ Failed to create secret"
        exit 1
    fi
fi

echo ""
echo "Secret Details:"
echo "  Name: $SECRET_NAME"
echo "  Region: $AWS_REGION"
echo "  Account: $SF_ACCOUNT"
echo "  Database: $SF_DATABASE"
echo "  Warehouse: $SF_WAREHOUSE"
echo "  User: $SF_USER"
echo ""
echo "Next Steps:"
echo "1. Use this secret name when creating the QuickSight data source:"
echo "   python create_snowflake_datasource.py --secret-name $SECRET_NAME"
echo ""
echo "2. Or verify the secret:"
echo "   aws secretsmanager get-secret-value --secret-id $SECRET_NAME --region $AWS_REGION"
