"""
IoT Telemetry Simulator — Lambda function

Simulates 45 John Deere machines across 3 organizations sending near real-time
telemetry to Amazon Kinesis Data Streams.  Triggered every minute via EventBridge.

Each invocation generates 12 readings per machine (5-second intervals × 12 = 60 s),
covering the most recent minute.  Records are batch-written to Kinesis using
PutRecords (up to 500 records per call, 5 MB per call).

The payload schema matches the telemetry Iceberg table defined in
sql/01_create_telemetry_table.sql.
"""

import json
import math
import os
import random
import time
from datetime import datetime, timezone, timedelta

import boto3

KINESIS_STREAM_NAME = os.environ["KINESIS_STREAM_NAME"]
AWS_REGION = os.environ.get("AWS_REGION_NAME", "us-east-1")

kinesis = boto3.client("kinesis", region_name=AWS_REGION)

# ---------------------------------------------------------------------------
# Machine registry — matches demo_data/machines.csv
# Each entry: (principalId, organizationId, machine_type)
# machine_type drives realistic simulation profiles.
# ---------------------------------------------------------------------------
MACHINES = [
    # Harvest Ridge Farms (24104235-...)
    ("cb22d0bb-7363-4e3e-b18d-0271f4d494da", "24104235-a030-4aaf-bf4b-496cd3119b8d", "Combine"),
    ("afd283f8-dd32-4764-9b9b-5832c1d8f126", "24104235-a030-4aaf-bf4b-496cd3119b8d", "Nutrient Application"),
    ("90940690-a4cb-4d5f-bcdd-fc158316d0d2", "24104235-a030-4aaf-bf4b-496cd3119b8d", "Tractor"),
    ("13167566-30ba-44ff-9142-b54e40a54b51", "24104235-a030-4aaf-bf4b-496cd3119b8d", "Combine"),
    ("7ce87efe-6e34-47d9-9066-14088be7b70e", "24104235-a030-4aaf-bf4b-496cd3119b8d", "Sprayer"),
    ("a2038a8c-9f3a-4dc3-b837-9b503e8d647a", "24104235-a030-4aaf-bf4b-496cd3119b8d", "Tractor"),
    ("b345e772-f342-41cf-8495-14dd5b7f3023", "24104235-a030-4aaf-bf4b-496cd3119b8d", "Tractor"),
    ("6e8362dd-8f4d-4ec0-9df5-8f5d9e248f70", "24104235-a030-4aaf-bf4b-496cd3119b8d", "Track Tractor"),
    ("ac9efca3-0f49-4288-ba41-537fab4a752b", "24104235-a030-4aaf-bf4b-496cd3119b8d", "Track Tractor"),
    ("94753b7b-4d32-4b8d-8882-f9a81670f8bf", "24104235-a030-4aaf-bf4b-496cd3119b8d", "Sprayer"),
    ("75c8ddd7-7620-4dd6-b397-1fa5fd6a149d", "24104235-a030-4aaf-bf4b-496cd3119b8d", "Nutrient Application"),
    ("d2fde32b-8939-4a2d-8cca-bef20515bcff", "24104235-a030-4aaf-bf4b-496cd3119b8d", "Combine"),
    ("913b5e3f-fa95-4774-9e3d-91da23afbed1", "24104235-a030-4aaf-bf4b-496cd3119b8d", "Nutrient Application"),
    # Prairie Wind Agriculture (135293da-...)
    ("a58ffd4c-53b7-41c1-8025-3eb5bd98d591", "135293da-8fbf-4191-8376-2e1293f0e48c", "Tractor"),
    ("18dab155-0d44-4d31-b6d9-4d8956639bcd", "135293da-8fbf-4191-8376-2e1293f0e48c", "Track Tractor"),
    ("c1e4c9fa-b8f3-4250-b1b5-d58fc3d63c71", "135293da-8fbf-4191-8376-2e1293f0e48c", "Sprayer"),
    ("57006824-f9cd-4d21-96fc-b198eac06423", "135293da-8fbf-4191-8376-2e1293f0e48c", "Sprayer"),
    ("da7e6907-8674-44c0-9560-ce427e094053", "135293da-8fbf-4191-8376-2e1293f0e48c", "Sprayer"),
    ("e2220f6e-374d-405e-80ce-ed19bfb26d39", "135293da-8fbf-4191-8376-2e1293f0e48c", "Sprayer"),
    ("b8355033-2541-4f8e-a471-1ffda87bfff2", "135293da-8fbf-4191-8376-2e1293f0e48c", "Track Tractor"),
    ("984c9f64-317e-4b1a-927d-5f61c2c5efea", "135293da-8fbf-4191-8376-2e1293f0e48c", "Track Tractor"),
    ("46ceff3a-51d0-4077-954c-0892d7eeeb90", "135293da-8fbf-4191-8376-2e1293f0e48c", "Combine"),
    ("e5d157c2-73a5-4376-9783-4d9c5afaa54d", "135293da-8fbf-4191-8376-2e1293f0e48c", "Nutrient Application"),
    ("068c1ca5-29b2-463d-a197-b2eee3735b09", "135293da-8fbf-4191-8376-2e1293f0e48c", "Sprayer"),
    ("8bee619d-0c92-4ae5-98e6-8c1b9d136db1", "135293da-8fbf-4191-8376-2e1293f0e48c", "Sprayer"),
    ("ab4e08b2-f275-42dd-bbde-3aef8ab2ca2b", "135293da-8fbf-4191-8376-2e1293f0e48c", "Sprayer"),
    ("7167c727-02b9-43cc-b938-73446fe83274", "135293da-8fbf-4191-8376-2e1293f0e48c", "Tractor"),
    ("4845da6d-edb7-490b-bafe-ae2970683b2c", "135293da-8fbf-4191-8376-2e1293f0e48c", "Tractor"),
    ("2d912b52-5638-4d4b-9705-ea7afda05350", "135293da-8fbf-4191-8376-2e1293f0e48c", "Tractor"),
    ("5f90f5b5-7f99-47d1-94cf-e2cfe2a68bf4", "135293da-8fbf-4191-8376-2e1293f0e48c", "Combine"),
    ("74fda278-9084-4c6a-adfd-561fedb923a2", "135293da-8fbf-4191-8376-2e1293f0e48c", "Tractor"),
    # Golden Acre Co-op (cacd5214-...)
    ("5e7537ff-c43b-4416-9ae5-beb7d7c2b35d", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Combine"),
    ("672690ec-0c6c-4138-95a3-4c866b3f0b8b", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Combine"),
    ("ba57fd4e-ea25-4c14-ad8a-dcb00f1bd26c", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Combine"),
    ("2bfaebaf-e3f0-4564-9660-f7e60002aa3e", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Sprayer"),
    ("1f42d0af-f9b5-4c8d-9361-a42a3918eb93", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Nutrient Application"),
    ("0d8663c4-a20a-47a6-9555-8358161e87ed", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Sprayer"),
    ("0f9a68bc-662f-4825-a1d8-cf2929393c88", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Sprayer"),
    ("f2a4d9a6-a17f-4cb0-8aac-db54837e5d6f", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Tractor"),
    ("e44df7f5-5775-4ba6-bf2b-83f4c01faa9c", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Combine"),
    ("29f07d99-8713-4b5a-a351-7c4b09f1f2ec", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Sprayer"),
    ("a0019ca5-d9cd-4c91-8dd4-55fb73ae1a0a", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Track Tractor"),
    ("6cfe3d2e-3f46-4750-aabb-74884832365c", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Sprayer"),
    ("d8d6dcde-74c7-4308-8128-3981bac49044", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Nutrient Application"),
    ("14e3e8e1-b544-46e4-b5ac-9cbf3e01d80e", "cacd5214-d0a9-4961-9b63-e1384dd89c4c", "Tractor"),
]

# Machine-type–specific simulation profiles.
# Probabilities: (WORKING, IDLE, TRANSPORT) — must sum to 1.
MACHINE_PROFILES = {
    "Combine": {
        "status_weights": [0.80, 0.15, 0.05],
        "autotrac_prob_while_working": 0.85,
        "section_control_prob": 0.80,
        "autopath_prob": 0.30,
        "fieldcruise_prob": 0.55,
        "ipm_prob": 0.40,
        "mfwd_prob": 0.00,
        "rear_pto_prob": 0.00,
        "wheel_slip_range": (1.5, 6.0),
    },
    "Sprayer": {
        "status_weights": [0.75, 0.10, 0.15],
        "autotrac_prob_while_working": 0.90,
        "section_control_prob": 0.88,
        "autopath_prob": 0.45,
        "fieldcruise_prob": 0.60,
        "ipm_prob": 0.35,
        "mfwd_prob": 0.00,
        "rear_pto_prob": 0.00,
        "wheel_slip_range": (0.5, 4.0),
    },
    "Tractor": {
        "status_weights": [0.70, 0.20, 0.10],
        "autotrac_prob_while_working": 0.70,
        "section_control_prob": 0.65,
        "autopath_prob": 0.20,
        "fieldcruise_prob": 0.40,
        "ipm_prob": 0.50,
        "mfwd_prob": 0.75,
        "rear_pto_prob": 0.45,
        "wheel_slip_range": (3.0, 12.0),
    },
    "Track Tractor": {
        "status_weights": [0.75, 0.18, 0.07],
        "autotrac_prob_while_working": 0.78,
        "section_control_prob": 0.72,
        "autopath_prob": 0.25,
        "fieldcruise_prob": 0.42,
        "ipm_prob": 0.55,
        "mfwd_prob": 0.00,
        "rear_pto_prob": 0.50,
        "wheel_slip_range": (1.0, 8.0),
    },
    "Nutrient Application": {
        "status_weights": [0.72, 0.12, 0.16],
        "autotrac_prob_while_working": 0.82,
        "section_control_prob": 0.78,
        "autopath_prob": 0.35,
        "fieldcruise_prob": 0.48,
        "ipm_prob": 0.38,
        "mfwd_prob": 0.60,
        "rear_pto_prob": 0.00,
        "wheel_slip_range": (2.0, 9.0),
    },
}

STATUSES = ["WORKING", "IDLE", "TRANSPORT"]
SAMPLE_INTERVAL_SEC = 5


def _machine_state(device_id: str, machine_type: str, ts: datetime) -> dict:
    """Generate a single telemetry reading for a machine at a given timestamp."""
    profile = MACHINE_PROFILES.get(machine_type, MACHINE_PROFILES["Tractor"])

    # Use device_id hash + minute to keep state sticky within a minute
    seed = hash(device_id + ts.strftime("%Y%m%d%H%M")) % (2**31)
    rng = random.Random(seed + int(ts.second / SAMPLE_INTERVAL_SEC))

    status = rng.choices(STATUSES, weights=profile["status_weights"], k=1)[0]
    is_working = status == "WORKING"

    # AutoTrac only active while WORKING
    autotrac = is_working and rng.random() < profile["autotrac_prob_while_working"]

    slip_min, slip_max = profile["wheel_slip_range"]
    # Add a small sinusoidal variation over time for visual interest in charts
    slip_base = slip_min + (slip_max - slip_min) * (0.5 + 0.5 * math.sin(ts.timestamp() / 300))
    wheel_slip = round(max(0.0, slip_base + rng.gauss(0, 0.5)), 1) if is_working else 0.0

    return {
        "device_id": device_id,
        "event_time": ts.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "machine_status": status,
        "autotrac_active": autotrac,
        "section_control_on": is_working and rng.random() < profile["section_control_prob"],
        "autopath_on": is_working and rng.random() < profile["autopath_prob"],
        "fieldcruise_on": is_working and rng.random() < profile["fieldcruise_prob"],
        "ipm_on": rng.random() < profile["ipm_prob"],
        "mfwd_on": rng.random() < profile["mfwd_prob"],
        "rear_pto_on": is_working and rng.random() < profile["rear_pto_prob"],
        "wheel_slip_pct": wheel_slip,
        "sample_interval_sec": SAMPLE_INTERVAL_SEC,
    }


def lambda_handler(event, context):
    now = datetime.now(timezone.utc)
    # Generate readings for the last 60 seconds (12 readings × 5-second intervals)
    timestamps = [
        now - timedelta(seconds=60 - (i * SAMPLE_INTERVAL_SEC))
        for i in range(12)
    ]

    records = []
    for device_id, org_id, machine_type in MACHINES:
        for ts in timestamps:
            reading = _machine_state(device_id, machine_type, ts)
            reading["organization_id"] = org_id
            reading["ingest_time"] = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            records.append({
                "Data": json.dumps(reading).encode("utf-8"),
                "PartitionKey": device_id,
            })

    # Kinesis PutRecords limit: 500 records per call, 5 MB per call
    batch_size = 400
    total_sent = 0
    failed = 0

    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        response = kinesis.put_records(StreamName=KINESIS_STREAM_NAME, Records=batch)
        failed += response.get("FailedRecordCount", 0)
        total_sent += len(batch) - response.get("FailedRecordCount", 0)

    print(
        f"Simulator: sent {total_sent} records "
        f"({len(MACHINES)} machines × 12 readings). "
        f"Failed: {failed}."
    )
    return {"sent": total_sent, "failed": failed}
