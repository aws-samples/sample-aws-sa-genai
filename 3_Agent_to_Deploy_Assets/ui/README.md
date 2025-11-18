# BIOPS React UI

Simple React application for managing BIOPS asset deployment jobs.

## Features

- **Job Creation Form**: Start new asset deployment jobs
- **Jobs List**: View all jobs with real-time status updates
- **Job Details**: Monitor step-by-step progress with logs
- **Auto-refresh**: Polls API every 5-10 seconds for updates

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure API endpoint:**
   ```bash
   cp .env.example .env
   # Edit .env with your API Gateway URL
   ```

3. **Run locally:**
   ```bash
   npm start
   ```

## Deployment

### Option 1: Automated Deployment
```bash
chmod +x deploy.sh
./deploy.sh https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
```

### Option 2: Manual Deployment
```bash
# Build
npm run build

# Deploy infrastructure
aws cloudformation deploy --template-file deploy.yaml --stack-name biops-ui-stack

# Upload files
aws s3 sync build/ s3://biops-ui-bucket --delete
```

## Components

- **App.js**: Main application with routing
- **JobForm.js**: Form to create new deployment jobs
- **JobsList.js**: List view of all jobs with status
- **JobDetail.js**: Detailed view of job steps and progress
- **api.js**: API service layer for backend communication

## API Integration

The UI integrates with the BIOPS API Gateway endpoints:
- `POST /jobs` - Create new job
- `GET /jobs` - List all jobs  
- `GET /jobs/{jobId}` - Get job details

## Real-time Updates

- Jobs list refreshes every 10 seconds
- Job details refresh every 5 seconds
- Status changes are reflected immediately