# 🚀 Automated S3 Bucket Cleanup Using AWS Lambda and Boto3

## 📌 Objective

Automate the **deletion of files older than 30 days** from an Amazon S3 bucket using **AWS Lambda** and **Boto3** (Python SDK for AWS).

This eliminates manual cleanup tasks and ensures storage cost optimization.

---

## 🏗️ Architecture

```
  CloudWatch / Manual Trigger
            ↓
       AWS Lambda
      (Python 3.12)
            ↓
      Boto3 S3 Client
            ↓
  ┌──────────────────────────────┐
  │       S3 Bucket              │
  │                              │
  │  old-file-1.txt (45 days)   │ → 🗑️ DELETED
  │  old-file-2.txt (60 days)   │ → 🗑️ DELETED
  │  old-file-3.txt (35 days)   │ → 🗑️ DELETED
  │  new-file-1.txt (5 days)    │ → ✅ KEPT
  │  new-file-2.txt (2 days)    │ → ✅ KEPT
  └──────────────────────────────┘
```

---

## ⚙️ Prerequisites

- AWS Account (Free Tier eligible)
- AWS Console access
- Basic understanding of:
  - Amazon S3
  - AWS Lambda
  - AWS IAM
  - Python

---

## 📋 Setup Steps

---

### 1️⃣ S3 Bucket Setup

1. Navigate to **S3 Dashboard → Create Bucket**
2. Configure:

| Setting              | Value                        |
|----------------------|------------------------------|
| Bucket Name          | `s3-auto-cleanup-siraj`      |
| Region               | `ap-south-1` (or your region)|
| Block Public Access  | ✅ Enabled                   |
| Versioning           | Disabled                     |

3. Click **Create Bucket**

#### Upload Test Files:

| File Name        | Purpose                      |
|------------------|------------------------------|
| `old-file-1.txt` | Simulated old file (>30 days)|
| `old-file-2.txt` | Simulated old file (>30 days)|
| `old-file-3.txt` | Simulated old file (>30 days)|
| `new-file-1.txt` | Recent file (keep)           |
| `new-file-2.txt` | Recent file (keep)           |

#### Upload via AWS CLI (Optional):
```bash
aws s3 cp old-file-1.txt s3://s3-auto-cleanup-siraj/
aws s3 cp old-file-2.txt s3://s3-auto-cleanup-siraj/
aws s3 cp old-file-3.txt s3://s3-auto-cleanup-siraj/
aws s3 cp new-file-1.txt s3://s3-auto-cleanup-siraj/
aws s3 cp new-file-2.txt s3://s3-auto-cleanup-siraj/
```

> ⚠️ **Note:** Since S3 uses upload time as `LastModified`, to simulate old files for testing, set `MAX_AGE_DAYS = 0` in the Lambda code temporarily. For production, use `MAX_AGE_DAYS = 30`.

---

### 2️⃣ IAM Role Setup

1. Go to **IAM Dashboard → Roles → Create Role**
2. Trusted Entity: **AWS Service → Lambda**
3. Attach Policy: **AmazonS3FullAccess**
4. Role Name: `Lambda-S3-Cleanup-Role`
5. Click **Create Role**

> ⚠️ Note: In production, use a custom policy with least privilege access instead of AmazonS3FullAccess.

---

### 3️⃣ Lambda Function Setup

1. Go to **Lambda Dashboard → Create Function**
2. Configure:

| Setting        | Value                      |
|----------------|----------------------------|
| Function Name  | `S3-Auto-Cleanup`          |
| Runtime        | Python 3.12                |
| Architecture   | x86_64                     |
| Execution Role | `Lambda-S3-Cleanup-Role`   |

3. Click **Create Function**

4. Configure Timeout:
   - **Configuration → General Configuration → Edit**
   - Timeout: **60 seconds**
   - Memory: **128 MB**

---

## 💻 Lambda Function Code

```python
import boto3
from datetime import datetime, timezone, timedelta

def lambda_handler(event, context):

    # =============================================
    # CONFIGURATION
    # =============================================
    BUCKET_NAME = 's3-auto-cleanup-siraj'   # Change to your bucket name
    MAX_AGE_DAYS = 30                        # Delete files older than 30 days

    print(f"Bucket: {BUCKET_NAME}")
    print(f"Max Age: {MAX_AGE_DAYS} days")
    print(f"Current Time: {datetime.now(timezone.utc)}")

    # =============================================
    # INITIALIZE S3 CLIENT
    # =============================================
    s3 = boto3.client('s3')

    # =============================================
    # LIST ALL OBJECTS IN BUCKET
    # =============================================
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
    except Exception as e:
        print(f"Error accessing bucket: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }

    # Check if bucket has objects
    if 'Contents' not in response:
        print("Bucket is empty. Nothing to clean up.")
        return {
            'statusCode': 200,
            'body': 'Bucket is empty.'
        }

    # =============================================
    # PROCESS OBJECTS
    # =============================================
    total_objects = len(response['Contents'])
    deleted_files = []
    kept_files = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

    print(f"Total objects found: {total_objects}")
    print(f"Cutoff date: {cutoff_date}")
    print("=" * 60)

    for obj in response['Contents']:
        file_key = obj['Key']
        last_modified = obj['LastModified']
        file_size = obj['Size']
        age_days = (datetime.now(timezone.utc) - last_modified).days

        print(f"File: {file_key}")
        print(f"   Last Modified: {last_modified}")
        print(f"   Age: {age_days} days")
        print(f"   Size: {file_size} bytes")

        if last_modified < cutoff_date:
            # DELETE old file
            s3.delete_object(Bucket=BUCKET_NAME, Key=file_key)
            deleted_files.append(file_key)
            print(f"   DELETED (older than {MAX_AGE_DAYS} days)")
        else:
            kept_files.append(file_key)
            print(f"   KEPT (within {MAX_AGE_DAYS} days)")

        print("-" * 40)

    # =============================================
    # SUMMARY
    # =============================================
    print("=" * 60)
    print(f"CLEANUP SUMMARY")
    print(f"   Total Objects Scanned: {total_objects}")
    print(f"   Files Deleted: {len(deleted_files)}")
    print(f"   Files Kept: {len(kept_files)}")

    if deleted_files:
        print(f"   Deleted Files: {deleted_files}")
    if kept_files:
        print(f"   Kept Files: {kept_files}")

    return {
        'statusCode': 200,
        'body': {
            'total_scanned': total_objects,
            'deleted_count': len(deleted_files),
            'kept_count': len(kept_files),
            'deleted_files': deleted_files,
            'kept_files': kept_files
        }
    }
```

---

## 🧪 Code Explanation

| Step | Description                                                    |
|------|----------------------------------------------------------------|
| 1    | Configure bucket name and max age threshold (30 days)          |
| 2    | Initialize Boto3 S3 client                                     |
| 3    | List all objects in the S3 bucket using `list_objects_v2()`    |
| 4    | Check if bucket is empty                                       |
| 5    | Calculate cutoff date (current time - 30 days)                 |
| 6    | Iterate through each object in the bucket                      |
| 7    | Compare `LastModified` date with cutoff date                   |
| 8    | Delete objects older than 30 days using `delete_object()`      |
| 9    | Keep objects newer than 30 days                                |
| 10   | Log all file details (name, age, size, action taken)           |
| 11   | Print cleanup summary with counts                              |
| 12   | Return JSON response with deleted and kept file lists          |

---

## 🧪 Testing Steps

### Manual Invocation

1. Go to **Lambda → S3-Auto-Cleanup → Test**
2. Create test event:
   - Event Name: `TestCleanup`
   - Event JSON: `{}`
3. Click **Test**

### Testing with Recently Uploaded Files

Since all files were just uploaded, temporarily change:

```python
MAX_AGE_DAYS = 0   # Deletes ALL files (for testing only)
```

Click **Deploy → Test**

> ⚠️ Remember to change back to `MAX_AGE_DAYS = 30` after testing.

### Expected Output (Production - 30 days)

```json
{
  "statusCode": 200,
  "body": {
    "total_scanned": 5,
    "deleted_count": 3,
    "kept_count": 2,
    "deleted_files": ["old-file-1.txt", "old-file-2.txt", "old-file-3.txt"],
    "kept_files": ["new-file-1.txt", "new-file-2.txt"]
  }
}
```

### Expected Output (Testing - 0 days)

```json
{
  "statusCode": 200,
  "body": {
    "total_scanned": 5,
    "deleted_count": 5,
    "kept_count": 0,
    "deleted_files": ["old-file-1.txt", "old-file-2.txt", "old-file-3.txt", "new-file-1.txt", "new-file-2.txt"],
    "kept_files": []
  }
}
```

### CloudWatch Logs Sample

```
Bucket: s3-auto-cleanup-siraj
Max Age: 30 days
Total objects found: 5
File: old-file-1.txt
   Last Modified: 2025-04-15 10:30:00+00:00
   Age: 45 days
   DELETED (older than 30 days)
File: new-file-1.txt
   Last Modified: 2025-05-28 14:00:00+00:00
   Age: 5 days
   KEPT (within 30 days)
CLEANUP SUMMARY
   Total Objects Scanned: 5
   Files Deleted: 3
   Files Kept: 2
```

### S3 Dashboard Verification

| File Name        | Before Lambda | After Lambda |
|------------------|---------------|--------------|
| old-file-1.txt   | Present       | **Deleted**  |
| old-file-2.txt   | Present       | **Deleted**  |
| old-file-3.txt   | Present       | **Deleted**  |
| new-file-1.txt   | Present       | **Present**  |
| new-file-2.txt   | Present       | **Present**  |

---

## 📸 Screenshots Checklist

| #  | Screenshot                                              |
|----|---------------------------------------------------------|
| 1  | S3 Dashboard - Bucket created                           |
| 2  | S3 Bucket - Files uploaded (before cleanup)             |
| 3  | IAM Role - Lambda-S3-Cleanup-Role created               |
| 4  | IAM Role - AmazonS3FullAccess policy attached           |
| 5  | Lambda Function - Code editor with Python code          |
| 6  | Lambda Function - Configuration (timeout/memory)        |
| 7  | Lambda Function - Test event created                    |
| 8  | Lambda Function - Test execution result (success)       |
| 9  | CloudWatch Logs - File details and deletion logs        |
| 10 | S3 Bucket - After cleanup (old files deleted)           |

---

## ⚠️ Challenges Faced & Solutions

### 1. Simulating Old Files
- **Problem:** S3 uses upload timestamp as `LastModified`, so freshly uploaded files appear as new
- **Solution:** Temporarily set `MAX_AGE_DAYS = 0` for testing to demonstrate deletion functionality

### 2. Bucket Region Mismatch
- **Problem:** Lambda could not access S3 bucket in a different region
- **Solution:** Ensured Lambda and S3 bucket are in the same AWS region

### 3. Lambda Timeout
- **Problem:** Default 3-second timeout was insufficient for buckets with many files
- **Solution:** Increased timeout to 60 seconds

### 4. Permission Issues
- **Problem:** Lambda could not list or delete S3 objects
- **Solution:** Attached `AmazonS3FullAccess` policy to Lambda execution role

### 5. Pagination for Large Buckets
- **Problem:** `list_objects_v2()` returns max 1000 objects per call
- **Solution:** For production, implement pagination using `ContinuationToken` (noted as future enhancement)

---

## 🛠️ Technologies Used

| Technology     | Purpose                                    |
|----------------|--------------------------------------------|
| Amazon S3      | Object storage for files                   |
| AWS Lambda     | Serverless compute for automation          |
| AWS IAM        | Role-based access control                  |
| AWS CloudWatch | Logging and monitoring                     |
| Python 3.12    | Lambda runtime language                    |
| Boto3          | AWS SDK for Python                         |

---

## 🎯 Learning Outcomes

- Understanding of AWS Lambda serverless architecture
- Hands-on experience with Boto3 SDK for S3 operations
- S3 object lifecycle management
- IAM role creation and permission management
- CloudWatch log analysis and debugging
- Date/time handling in Python for file age calculation
- Infrastructure automation best practices

---

## ⭐ Future Enhancements

- Add **CloudWatch EventBridge** rule for daily scheduled cleanup
- Implement **SNS notifications** when files are deleted
- Create **custom IAM policy** with least privilege access
- Add **pagination support** for buckets with 1000+ objects
- Implement **dry-run mode** to preview deletions before executing
- Add **folder-specific cleanup** (process only certain prefixes)
- Implement **S3 Lifecycle Policies** as alternative approach
- Add **Terraform/CloudFormation** templates for infrastructure as code

---

## 📎 Project Structure

```
aws-s3-auto-cleanup/
├── lambda_function.py     # Lambda function code
├── README.md              # Documentation (this file)
└── screenshots/           # Screenshots folder
    ├── s3-bucket-created.png
    ├── s3-files-uploaded.png
    ├── iam-role.png
    ├── lambda-code.png
    ├── lambda-config.png
    ├── lambda-test-result.png
    ├── cloudwatch-logs.png
    └── s3-after-cleanup.png
```

---

## 👤 Author

**Sirajuddin Mohammed**
IT Engineer | DevOps | Cloud | SRE

---

## 📝 Important Notes

> ⚠️ **Bucket Name:** Update `BUCKET_NAME` in the code to match your actual S3 bucket name.

> ⚠️ **Region:** Ensure Lambda function and S3 bucket are in the same AWS region.

> ⚠️ **Testing:** Use `MAX_AGE_DAYS = 0` for testing. Change back to `30` for production.

> ⚠️ **Cleanup:** Delete the S3 bucket and Lambda function after testing to avoid charges.

> ⚠️ **Security:** In production, replace `AmazonS3FullAccess` with a custom least-privilege policy.

> ⚠️ **Large Buckets:** For buckets with more than 1000 objects, implement pagination in the code.

---

✅ **Project successfully demonstrates automated S3 bucket cleanup using AWS Lambda and Boto3.**
