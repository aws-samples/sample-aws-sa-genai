# IoT Near Real-Time Analytics Pipeline

Converts the John Deere Work Overview demo from static CSV tables to a live
streaming IoT pipeline, while keeping all non-telemetry tables static.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LIVE INGESTION PATH                              │
│                                                                         │
│  Lambda Simulator ──► Kinesis Data Streams ──► Data Firehose           │
│  (45 machines,         (iot-telemetry-stream)    (60s buffer)          │
│   every 1 min,                                       │                 │
│   12 readings/machine)                               ▼                 │
│                                            S3 Tables: telemetry        │
│                                            (raw 5-sec readings)        │
│                                                       │                │
│                              EventBridge (hourly) ────┘                │
│                                    │                                   │
│                                    ▼                                   │
│                          Lambda ELT Processor                          │
│                          (Athena DELETE + INSERT)                      │
│                                    │                                   │
│                                    ▼                                   │
│                          S3 Tables: measurements                       │
│                          (hourly aggregated telemetry)                 │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     STATIC REFERENCE TABLES (Athena External)           │
│                                                                         │
│  organizations │ clients │ farms │ fields │ machines │ machine_tags    │
│  scuds │ histogram │ field_operation_products                           │
│                                                                         │
│  Stored as CSV in S3, registered as Athena external tables in the       │
│  same iot_analytics database — queryable via QuickSight runtime-join.   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

| Layer | Service | Latency | Description |
|-------|---------|---------|-------------|
| Ingest | Lambda → Kinesis | < 1s | 45 machines × 12 readings/min |
| Buffer | Kinesis → Firehose | 1–5s | ON_DEMAND stream |
| Deliver | Firehose → S3 Tables | 60–90s | Iceberg format, 64 MB buffer |
| ELT | Lambda → Athena → S3 Tables | ~5 min/hour | Hourly aggregation |

## Table Schemas

### `telemetry` (S3 Tables / Iceberg — LIVE)
One row per 5-second reading per machine. Written by Firehose.

| Column | Type | Description |
|--------|------|-------------|
| `device_id` | STRING | Machine principalId (FK → machines) |
| `organization_id` | STRING | FK → organizations |
| `event_time` | TIMESTAMP | Reading timestamp (UTC) |
| `ingest_time` | TIMESTAMP | Kinesis ingestion time |
| `machine_status` | STRING | WORKING / IDLE / TRANSPORT |
| `autotrac_active` | BOOLEAN | AutoTrac guidance engaged |
| `section_control_on` | BOOLEAN | Boom section control active |
| `autopath_on` | BOOLEAN | AutoPath active |
| `fieldcruise_on` | BOOLEAN | FieldCruise active |
| `ipm_on` | BOOLEAN | IPM active |
| `mfwd_on` | BOOLEAN | MFWD engaged |
| `rear_pto_on` | BOOLEAN | Rear PTO active |
| `wheel_slip_pct` | DOUBLE | Wheel slip % |
| `sample_interval_sec` | INT | Seconds this reading covers (5) |

### `measurements` (S3 Tables / Iceberg — ELT output)
Schema matches the static `measurements.csv` — one row per hour × machine.
QuickSight dashboards built on the static data work without changes.

---

## Simulator Alternatives

You don't have physical IoT devices — here are your options, ranked by effort:

### Option 1: Lambda (included) ✓
EventBridge triggers the simulator Lambda every minute. Zero infrastructure to
manage. Starts immediately after `deploy.sh`.

### Option 2: AWS Kinesis Data Generator (KDG)
Free, browser-based tool hosted by AWS. No code needed for demos.

1. Open: https://kdg.us-east-1.amazonaws.com/  (or your region's URL)
2. Sign in with your AWS credentials
3. Set stream: `iot-telemetry-stream`, region: `us-east-1`
4. Use this template in the KDG console:

```json
{
  "device_id": "{{random.arrayElement(['cb22d0bb-7363-4e3e-b18d-0271f4d494da','13167566-30ba-44ff-9142-b54e40a54b51','7ce87efe-6e34-47d9-9066-14088be7b70e'])}}",
  "organization_id": "24104235-a030-4aaf-bf4b-496cd3119b8d",
  "event_time": "{{date.now('YYYY-MM-DDTHH:mm:ss')}}Z",
  "ingest_time": "{{date.now('YYYY-MM-DDTHH:mm:ss')}}Z",
  "machine_status": "{{random.arrayElement(['WORKING','WORKING','WORKING','IDLE','TRANSPORT'])}}",
  "autotrac_active": {{random.boolean}},
  "section_control_on": {{random.boolean}},
  "autopath_on": {{random.boolean}},
  "fieldcruise_on": {{random.boolean}},
  "ipm_on": {{random.boolean}},
  "mfwd_on": {{random.boolean}},
  "rear_pto_on": {{random.boolean}},
  "wheel_slip_pct": {{random.number({"min":0,"max":15,"precision":0.1})}},
  "sample_interval_sec": 5
}
```

Advantage: great for demos where you want to show the tool visually.

### Option 3: AWS Fargate (ECS Task) — persistent simulator
Use this if you want the simulator to run 24/7 without Lambda cold starts or
the 15-minute timeout limit.

1. Build a Docker image from `lambda/simulator/handler.py` with a `while True: sleep(60)` loop
2. Push to Amazon ECR
3. Create an ECS Fargate task with the container
4. Run as a service — always-on, scales to 0 cost when stopped

Best for: realistic long-running demo environments or load testing.

### Option 4: AWS Step Functions Express Workflows
Model each machine as a separate state machine branch. Use `Map` state to fan
out 45 concurrent machine simulators. Schedule with EventBridge.

Best for: demos where you want to show Step Functions or need per-machine
workflow branching logic (e.g., "machine breaks down → enters maintenance mode").

### Option 5: Amazon EventBridge Pipes + Lambda
A slightly cleaner serverless alternative to direct EventBridge → Lambda if you
want built-in filtering and enrichment between Kinesis and downstream processing.

---

## Deployment

### Prerequisites
- AWS CLI v2 configured (`aws configure`)
- Python 3.9+ and pip
- QuickSight Enterprise Edition (for Direct Query on S3 Tables)
- S3 Tables available in your region (us-east-1 recommended)

### Steps

```bash
# 1. Copy and fill in configuration
cp config.env.template config.env
# Edit config.env: set ACCOUNT_ID and review bucket names

# 2. Source config
source config.env

# 3. Deploy all resources (runs steps 1–8 in sequence)
bash deploy.sh

# 4. Verify telemetry is flowing (~2 minutes after deploy)
aws athena start-query-execution \
  --query-string "SELECT COUNT(*) FROM iot_analytics.telemetry" \
  --result-configuration "OutputLocation=s3://${ATHENA_OUTPUT_BUCKET}/verify/"

# 5. Manually trigger ELT for the current hour (for testing)
aws lambda invoke \
  --function-name iot-telemetry-elt-processor \
  --payload '{"hour_offset": 0}' \
  /tmp/elt-response.json && cat /tmp/elt-response.json

# 6. Tear down when done
bash teardown.sh
```

### Run a single step
```bash
bash deploy.sh --step 1   # IAM roles only
bash deploy.sh --step 4   # S3 Tables only
bash deploy.sh --step 8   # Lambda functions only
```

---

## Connecting QuickSight

1. In QuickSight → Manage QuickSight → Security & permissions → enable S3 Tables
2. New dataset → "Amazon S3 Tables (Apache Iceberg)"
3. Select table bucket `iot-demo-tables-ACCOUNT_ID`, database `iot_analytics`
4. **Select "Directly query your data"** (not SPICE) for live data
5. For static tables (organizations, machines, etc.) connect via Athena as a
   separate data source pointing to the same `iot_analytics` Glue database

### Runtime-join configuration (same as existing demo)
All existing join paths from the multi-table demo continue to work unchanged:
- `measurements.machine_id = machines.principalId`
- `machines.principalId = machine_tags.machine_id`
- `histogram.fieldOperationGUID = field_operation_products.field_operation_guid`

The only difference: `measurements` now comes from live S3 Tables instead of
a static CSV.

---

## Monitoring

| What to check | Where |
|---------------|-------|
| Kinesis IncomingRecords | CloudWatch → Kinesis → `iot-telemetry-stream` |
| Firehose delivery freshness | CloudWatch → Firehose → `DataFreshness` (should be < 90s) |
| Firehose errors | CloudWatch Logs → `/aws/firehose/iot-telemetry-firehose` |
| Lambda simulator runs | CloudWatch Logs → `/aws/lambda/iot-telemetry-simulator` |
| ELT runs | CloudWatch Logs → `/aws/lambda/iot-telemetry-elt-processor` |
| Telemetry row count | Athena: `SELECT COUNT(*) FROM iot_analytics.telemetry` |
| Measurements row count | Athena: `SELECT COUNT(*) FROM iot_analytics.measurements` |
