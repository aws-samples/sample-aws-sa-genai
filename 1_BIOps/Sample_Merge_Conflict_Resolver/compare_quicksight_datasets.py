# compare_quicksight_datasets.py

import boto3
import json
import os
from datetime import datetime

def get_dataset_description_from_api(account_id, dataset_id, region):
    client = boto3.client('quicksight', region_name=region)
    response = client.describe_data_set(
        AwsAccountId=account_id,
        DataSetId=dataset_id
    )
    return response['DataSet']

def default_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")




def get_dataset_description_from_file(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def compare_output_columns(old_dataset, new_dataset):
    old_columns = {col["Name"]: col["Type"] for col in old_dataset.get("OutputColumns", [])}
    new_columns = {col["Name"]: col["Type"] for col in new_dataset.get("OutputColumns", [])}

    changes = {
        "datatype_changes": [],
        "added_columns": [],
        "removed_columns": []
    }

    for name, old_type in old_columns.items():
        new_type = new_columns.get(name)
        if new_type is None:
            changes["removed_columns"].append(name)
        elif new_type != old_type:
            changes["datatype_changes"].append({
                "ColumnName": name,
                "OldType": old_type,
                "NewType": new_type
            })

    for name in new_columns:
        if name not in old_columns:
            changes["added_columns"].append({
                "ColumnName": name,
                "NewType": new_columns[name]
            })

    return changes

if __name__ == "__main__":
    # Load environment variables
    account_id = os.getenv('QUICKSIGHT_ACCOUNT_ID')
    new_dataset_id = os.getenv('NEW_DATASET_ID')
    region = os.getenv('AWS_REGION', 'us-east-1')
    old_json_path = f"{new_dataset_id}.json"  # Default to a local file

    

    if not all([account_id, new_dataset_id]):
        raise ValueError("Missing required environment variables (QUICKSIGHT_ACCOUNT_ID, NEW_DATASET_ID)")
        
    ds = get_dataset_description_from_api(account_id, new_dataset_id, region)


    with open(f"{new_dataset_id}.json", "w") as f:
        json.dump(ds, f, indent=4, default=default_serializer)

    # Load old dataset from file
    old_ds = get_dataset_description_from_file(old_json_path)

    # Load new dataset from QuickSight API
    new_ds = get_dataset_description_from_api(account_id, new_dataset_id, region)

    # Compare
    result = compare_output_columns(old_ds, new_ds)

    # Print result
    print("\n--- Comparison Results ---")
    if result["datatype_changes"]:
        print("🛠️ Data Type Changes:")
        for c in result["datatype_changes"]:
            print(f"- {c['ColumnName']}: {c['OldType']} → {c['NewType']}")
    if result["added_columns"]:
        print("\n➕ Added Columns:")
        for c in result["added_columns"]:
            print(f"- {c['ColumnName']}: {c['NewType']}")
    if result["removed_columns"]:
        print("\n➖ Removed Columns:")
        for name in result["removed_columns"]:
            print(f"- {name}")
    if not any(result.values()):
        print("No differences detected.")

    # Save result as JSON
    with open('quicksight_column_diff.json', 'w') as f:
        json.dump(result, f, indent=4)



        