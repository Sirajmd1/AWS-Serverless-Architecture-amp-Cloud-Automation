# Assignment 4: Automatic EBS Snapshot and Cleanup Using AWS Lambda and Boto3

## Objective
Automate the backup lifecycle for an Amazon EBS volume using **AWS Lambda** and **Boto3** by:
- creating snapshots for a specified EBS volume, and
- deleting snapshots older than **30 days** to reduce storage costs.

---

## Solution Overview
This project uses an AWS Lambda function written in Python to:
1. Connect to AWS EC2 using the **Boto3** SDK
2. Create a new snapshot for a specified EBS volume
3. Retrieve existing snapshots for that volume
4. Delete snapshots older than **30 days**
5. Log created and deleted snapshot IDs in **Amazon CloudWatch Logs**

---

## AWS Services Used
- **Amazon EC2 / EBS** – to manage storage volumes and snapshots
- **AWS Lambda** – to run the snapshot and cleanup automation
- **AWS IAM** – to provide permissions to Lambda
- **Amazon EventBridge (CloudWatch Events)** – to schedule automatic execution
- **Amazon CloudWatch Logs** – to monitor Lambda execution logs

---

## Prerequisites
Before starting, ensure you have:
- An active AWS account
- At least one existing **EBS volume**
- Basic access to **IAM**, **Lambda**, and **EC2**
- The **Volume ID** of the EBS volume you want to back up

Example Volume ID:
```text
vol-0abc1234def567890
```

---

## Architecture Flow
1. User identifies the target EBS volume
2. Lambda function is created with an IAM role
3. Lambda uses Boto3 to create a snapshot of the volume
4. Lambda checks existing snapshots for the same volume
5. Any snapshot older than 30 days is deleted
6. Snapshot activity is logged in CloudWatch
7. (Optional) EventBridge triggers the Lambda weekly

---

## Step 1: Identify the EBS Volume
1. Open the **AWS Management Console**
2. Navigate to **EC2 Dashboard**
3. In the left navigation pane, click **Volumes**
4. Select the EBS volume you want to back up
5. Copy the **Volume ID**

---

## Step 2: Create IAM Role for Lambda
1. Open the **IAM Console**
2. Go to **Roles** → **Create role**
3. Select **AWS service**
4. Choose **Lambda**
5. Attach the policy:
   - `AmazonEC2FullAccess` *(used here for assignment simplicity)*
6. Name the role:
   ```text
   lambda-ebs-snapshot-role
   ```
7. Click **Create role**

> **Note:** In production, a least-privilege custom policy should be used instead of full EC2 access.

---

## Step 3: Create the Lambda Function
1. Open the **AWS Lambda Console**
2. Click **Create function**
3. Select **Author from scratch**
4. Configure the function:
   - **Function name:** `EBS-Snapshot-Cleanup`
   - **Runtime:** `Python 3.x`
5. Under **Permissions**, choose:
   - **Use an existing role**
   - Select `lambda-ebs-snapshot-role`
6. Click **Create function**

---

## Step 4: Lambda Function Code
Replace the default Lambda code with the script below.

```python
import boto3
from datetime import datetime, timezone, timedelta

# Initialize EC2 client
ec2 = boto3.client('ec2')

# Replace with your actual EBS Volume ID
VOLUME_ID = 'vol-0abc1234def567890'
RETENTION_DAYS = 30

def lambda_handler(event, context):
    created_snapshot_id = None
    deleted_snapshots = []

    try:
        # Create a new snapshot
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

        # Calculate snapshot retention cutoff date
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

        # List all snapshots for this volume owned by this account
        snapshots = ec2.describe_snapshots(
            OwnerIds=['self'],
            Filters=[
                {'Name': 'volume-id', 'Values': [VOLUME_ID]}
            ]
        )['Snapshots']

        # Delete snapshots older than retention period
        for snapshot in snapshots:
            snapshot_id = snapshot['SnapshotId']
            start_time = snapshot['StartTime']

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
```

---

## Step 5: Deploy the Function
1. Paste the code into the Lambda code editor
2. Replace the placeholder volume ID with your actual volume ID
3. Click **Deploy**

---

## Step 6: Manual Testing
1. In the Lambda console, click **Test**
2. Create a new test event with the following payload:

```json
{}
```

3. Click **Test** again to invoke the function

### Expected Result
```json
{
  "statusCode": 200,
  "body": {
    "message": "Snapshot creation and cleanup completed successfully",
    "created_snapshot": "snap-0123456789abcdef0",
    "deleted_snapshots": [
      "snap-0fedcba9876543210"
    ]
  }
}
```

---

## Step 7: Verify Snapshot Creation and Cleanup
### Verify Snapshot Creation
1. Go to **EC2 Dashboard**
2. Click **Snapshots**
3. Search using the new snapshot ID or volume ID

### Verify Snapshot Cleanup
- Confirm that snapshots older than **30 days** are deleted
- Review **CloudWatch Logs** for created and deleted snapshot IDs

---

## Step 8: Automate Using EventBridge (Bonus)
To run the Lambda function automatically every week:

1. Open the Lambda function
2. Click **Add trigger**
3. Select **EventBridge (CloudWatch Events)**
4. Create a new rule:
   - **Rule name:** `weekly-ebs-backup`
   - **Schedule expression:**

### Rate Expression
```text
rate(7 days)
```

### OR Cron Expression
Runs every Sunday at 12:00 UTC:
```text
cron(0 12 ? * SUN *)
```

5. Save the trigger

---

## Optional Enhancement: Use Environment Variables
Instead of hardcoding values, store them as Lambda environment variables.

### Add these variables under Lambda Configuration
- `VOLUME_ID = vol-0abc1234def567890`
- `RETENTION_DAYS = 30`

### Updated Code Snippet
```python
import boto3
import os
from datetime import datetime, timezone, timedelta

ec2 = boto3.client('ec2')

VOLUME_ID = os.environ['VOLUME_ID']
RETENTION_DAYS = int(os.environ.get('RETENTION_DAYS', '30'))

def lambda_handler(event, context):
    created_snapshot_id = None
    deleted_snapshots = []

    try:
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

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

        snapshots = ec2.describe_snapshots(
            OwnerIds=['self'],
            Filters=[
                {'Name': 'volume-id', 'Values': [VOLUME_ID]}
            ]
        )['Snapshots']

        for snapshot in snapshots:
            snapshot_id = snapshot['SnapshotId']
            start_time = snapshot['StartTime']

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
```

---

## Recommended Least-Privilege IAM Policy
For real-world usage, replace `AmazonEC2FullAccess` with a more restrictive custom policy like the following:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CreateDescribeDeleteSnapshots",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateSnapshot",
        "ec2:DeleteSnapshot",
        "ec2:DescribeSnapshots",
        "ec2:CreateTags"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Common Errors and Troubleshooting
### 1. UnauthorizedOperation
**Cause:** Lambda role does not have required permissions  
**Fix:** Attach `AmazonEC2FullAccess` or the required custom EC2 permissions

### 2. InvalidVolume.NotFound
**Cause:** Incorrect or non-existent volume ID  
**Fix:** Verify the exact EBS volume ID from the EC2 console

### 3. No Snapshots Deleted
**Cause:** No snapshots are older than 30 days  
**Fix:** This is expected behavior if all snapshots are within the retention period

### 4. Snapshot Deletion Fails
**Cause:** Snapshot may be referenced by an AMI or another dependency  
**Fix:** Ensure the snapshot is not in use before deletion

---

## Sample Output
```text
Created snapshot: snap-0123456789abcdef0
Deleted old snapshot: snap-0fedcba9876543210
```

---

## Conclusion
This project demonstrates how to automate **EBS snapshot creation and cleanup** using **AWS Lambda** and **Boto3**. The solution improves backup consistency, reduces manual effort, and helps control storage costs by automatically removing outdated snapshots.

---

## Deliverables Included
- AWS Lambda function using Python and Boto3
- Snapshot creation for a specified EBS volume
- Automatic deletion of snapshots older than 30 days
- Logging through CloudWatch Logs
- Optional scheduled execution using EventBridge

---

## Author
**Name:** Sirajuddin Mohammed  
**Assignment:** Assignment 4 – Automatic EBS Snapshot and Cleanup Using AWS Lambda and Boto3
