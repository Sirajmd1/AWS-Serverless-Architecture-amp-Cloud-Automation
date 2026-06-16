import boto3
from datetime import datetime, timezone, timedelta

# Initialize EC2 client
ec2 = boto3.client('ec2')

# Configuration
VOLUME_ID = 'vol-0d4de136ab5f74fb8'   # Replace with your actual Volume ID
RETENTION_DAYS = 30

def lambda_handler(event, context):
    created_snapshot_id = None
    deleted_snapshots = []

    try:
        # 1. Create snapshot
        description = f"Automated snapshot for {VOLUME_ID} on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        response = ec2.create_snapshot(
            VolumeId=VOLUME_ID,
            Description=description,
            TagSpecifications=[
                {
                    'ResourceType': 'snapshot',
                    'Tags': [
                        {'Key': 'CreatedBy', 'Value': 'Lambda'},
                        {'Key': 'VolumeId', 'Value': VOLUME_ID},
                        {'Key': 'Purpose', 'Value': 'AutomatedBackup'}
                    ]
                }
            ]
        )

        created_snapshot_id = response['SnapshotId']
        print(f"Created snapshot: {created_snapshot_id}")

        # 2. Calculate retention threshold
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

        # 3. List snapshots created by this account for the specific volume
        snapshots = ec2.describe_snapshots(
            OwnerIds=['self'],
            Filters=[
                {'Name': 'volume-id', 'Values': [VOLUME_ID]}
            ]
        )['Snapshots']

        # 4. Delete old snapshots
        for snapshot in snapshots:
            snapshot_id = snapshot['SnapshotId']
            start_time = snapshot['StartTime']  # timezone-aware datetime in UTC

            if start_time < cutoff_date:
                ec2.delete_snapshot(SnapshotId=snapshot_id)
                deleted_snapshots.append(snapshot_id)
                print(f"Deleted old snapshot: {snapshot_id}")

        return {
            'statusCode': 200,
            'body': {
                'message': 'Snapshot creation and cleanup completed successfully',
                'created_snapshot': created_snapshot_id,
                'deleted_snapshots': deleted_snapshots
            }
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': {
                'message': 'Error during snapshot creation/cleanup',
                'error': str(e)
            }
        }