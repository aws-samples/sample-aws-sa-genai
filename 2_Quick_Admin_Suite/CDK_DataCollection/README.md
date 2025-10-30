# Quick Admin Suite Data Collection - CDK

This CDK application converts the CloudFormation template for QuickSight Admin Suite data collection into AWS CDK Python code.

## Prerequisites

- Python 3.7+
- AWS CDK CLI installed (`npm install -g aws-cdk`)
- AWS credentials configured

## Setup

1. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Deploy

1. Bootstrap CDK (first time only):
```bash
cdk bootstrap
```

2. Deploy the stack:
```bash
cdk deploy
```

## Resources Created

- **IAM Role**: QuickSightAdminConsole2025 with necessary permissions
- **S3 Buckets**: Main admin console bucket and CloudWatch metrics buckets
- **Glue Jobs**: 7 ETL jobs for QuickSight data collection
- **Glue Triggers**: Scheduled triggers running every 3 hours
- **CloudWatch Metric Streams**: 5 streams for different QuickSight metrics
- **Kinesis Firehose**: Delivery streams for metric data to S3

## Cleanup

```bash
cdk destroy
```

## Differences from CloudFormation

- Uses CDK constructs for better type safety and IDE support
- Automatic dependency management
- Simplified resource references
- Built-in best practices for security and configuration