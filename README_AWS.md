# 🚀 AWS Lambda EC2 Auto-Manager

## 📌 Objective

Automate the **stopping and starting of EC2 instances** based on their tags using **AWS Lambda** and **Boto3** (Python SDK for AWS).

- Instances tagged with `Action = Auto-Stop` → **Automatically Stopped**
- Instances tagged with `Action = Auto-Start` → **Automatically Started**

---

## 🏗️ Architecture

```
  CloudWatch / Manual Trigger
            ↓
       AWS Lambda
      (Python 3.12)
            ↓
      Boto3 EC2 Client
            ↓
  ┌──────────────────────────┐
  │  Tag: Action = Auto-Stop  │ → STOP Instance
  │  Tag: Action = Auto-Start │ → START Instance
  └──────────────────────────┘
            ↓
       EC2 Instances
      (State Changed)
```

---

## ⚙️ Prerequisites

- AWS Account (Free Tier eligible)
- AWS Console access
- Basic understanding of:
  - EC2
  - IAM
  - Lambda
  - Python

---

## 📋 Setup Steps

---

### 1️⃣ EC2 Instance Setup

1. Navigate to **EC2 Dashboard → Launch Instance**
2. Create **two t2.micro instances**

| Instance Name       | Tag Key  | Tag Value   | Initial State |
|---------------------|----------|-------------|---------------|
| Auto-Stop-Instance  | `Action` | `Auto-Stop` | Running       |
| Auto-Start-Instance | `Action` | `Auto-Start`| Stopped       |

#### How to Add Tags:
- Select instance → **Tags tab → Manage Tags**
- Add:
  - Key: `Action`
  - Value: `Auto-Stop` or `Auto-Start`
- Click **Save**

---

### 2️⃣ IAM Role Setup

1. Go to **IAM Dashboard → Roles → Create Role**
2. Trusted Entity: **AWS Service → Lambda**
3. Attach Policy: **AmazonEC2FullAccess**
4. Role Name: `Lambda-EC2-Management-Role`
5. Click **Create Role**

> ⚠️ Note: In production environments, use a custom policy with least privilege access instead of AmazonEC2FullAccess.

---

### 3️⃣ Lambda Function Setup

1. Go to **Lambda Dashboard → Create Function**
2. Configure:

| Setting        | Value                          |
|----------------|--------------------------------|
| Function Name  | `EC2-Auto-Manager`             |
| Runtime        | Python 3.12                    |
| Architecture   | x86_64                         |
| Execution Role | `Lambda-EC2-Management-Role`   |

3. Click **Create Function**

4. Configure Timeout:
   - **Configuration → General Configuration → Edit**
   - Timeout: **30 seconds**
   - Memory: **128 MB**

---

## 💻 Lambda Function Code

```python
import boto3

def lambda_handler(event, context):
    
    # Auto-detect region
    session = boto3.session.Session()
    current_region = session.region_name
    print(f"Lambda running in region: {current_region}")
    
    ec2 = boto3.client('ec2', region_name=current_region)

    # =============================================
    # List ALL instances (for debugging)
    # =============================================
    all_instances = ec2.describe_instances()
    print(f"Total reservations found: {len(all_instances['Reservations'])}")
    
    for reservation in all_instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            state = instance['State']['Name']
            tags = instance.get('Tags', [])
            print(f"Instance: {instance_id} | State: {state} | Tags: {tags}")

    # =============================================
    # STOP instances tagged with Action = Auto-Stop
    # =============================================
    stop_response = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag:Action',
                'Values': ['Auto-Stop']
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ]
    )

    stop_instances = []
    for reservation in stop_response['Reservations']:
        for instance in reservation['Instances']:
            stop_instances.append(instance['InstanceId'])

    if stop_instances:
        ec2.stop_instances(InstanceIds=stop_instances)
        print(f"Stopping instances: {stop_instances}")
    else:
        print("No running instances found with Auto-Stop tag.")

    # =============================================
    # START instances tagged with Action = Auto-Start
    # =============================================
    start_response = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag:Action',
                'Values': ['Auto-Start']
            },
            {
                'Name': 'instance-state-name',
                'Values': ['stopped']
            }
        ]
    )

    start_instances = []
    for reservation in start_response['Reservations']:
        for instance in reservation['Instances']:
            start_instances.append(instance['InstanceId'])

    if start_instances:
        ec2.start_instances(InstanceIds=start_instances)
        print(f"Starting instances: {start_instances}")
    else:
        print("No stopped instances found with Auto-Start tag.")

    # =============================================
    # SUMMARY
    # =============================================
    return {
        'statusCode': 200,
        'body': {
            'stopped_instances': stop_instances,
            'started_instances': start_instances
        }
    }
```

---

## 🧪 Code Explanation

| Step | Description |
|------|-------------|
| 1    | Initialize Boto3 session and detect current AWS region |
| 2    | Create EC2 client using Boto3 |
| 3    | List all instances for debugging purposes |
| 4    | Filter instances with tag `Action = Auto-Stop` and state `running` |
| 5    | Stop those instances using `ec2.stop_instances()` |
| 6    | Filter instances with tag `Action = Auto-Start` and state `stopped` |
| 7    | Start those instances using `ec2.start_instances()` |
| 8    | Log all affected instance IDs |
| 9    | Return summary response with status code 200 |

---

## 🧪 Testing Steps

### Manual Invocation

1. Go to **Lambda → EC2-Auto-Manager → Test**
2. Create test event:
   - Event Name: `TestEvent`
   - Event JSON: `{}`
3. Click **Test**

### Expected Output

```json
{
  "statusCode": 200,
  "body": {
    "stopped_instances": ["i-0abc123def456"],
    "started_instances": ["i-0xyz789ghi012"]
  }
}
```

### CloudWatch Logs

```
Lambda running in region: ap-south-1
Total reservations found: 2
Instance: i-0abc123 | State: running  | Tags: [{'Key': 'Action', 'Value': 'Auto-Stop'}]
Instance: i-0xyz789 | State: stopped  | Tags: [{'Key': 'Action', 'Value': 'Auto-Start'}]
Stopping instances: ['i-0abc123']
Starting instances: ['i-0xyz789']
```

### EC2 Dashboard Verification

| Instance             | Before Lambda | After Lambda |
|----------------------|---------------|--------------|
| Auto-Stop-Instance   | Running       | **Stopped**  |
| Auto-Start-Instance  | Stopped       | **Running**  |

---

## 📸 Screenshots Checklist

| #  | Screenshot                                          |
|----|-----------------------------------------------------|
| 1  | EC2 Dashboard - Both instances with tags visible     |
| 2  | EC2 Tags - Action = Auto-Stop                        |
| 3  | EC2 Tags - Action = Auto-Start                       |
| 4  | IAM Role - Lambda-EC2-Management-Role                |
| 5  | IAM Role - AmazonEC2FullAccess policy attached       |
| 6  | Lambda Function - Code editor                        |
| 7  | Lambda Function - Configuration (timeout/memory)     |
| 8  | Lambda Function - Test execution result (success)    |
| 9  | CloudWatch Logs - Instance IDs logged                |
| 10 | EC2 Dashboard - Auto-Stop instance STOPPED           |
| 11 | EC2 Dashboard - Auto-Start instance RUNNING          |

---

## ⚠️ Challenges Faced & Solutions

### 1. Region Mismatch
- **Problem:** Lambda was querying `us-east-1` but instances were in `ap-south-1`
- **Solution:** Used `boto3.session.Session().region_name` for auto-detection

### 2. Tag Key/Value Case Sensitivity
- **Problem:** Tags are case-sensitive (`action` ≠ `Action`)
- **Solution:** Ensured exact match: Key = `Action`, Value = `Auto-Stop` / `Auto-Start`

### 3. Instance State Filter
- **Problem:** Lambda skipped instances because state didn't match filter
- **Solution:** Ensured Auto-Stop instance was Running and Auto-Start instance was Stopped before testing

### 4. Lambda Timeout
- **Problem:** Default 3-second timeout was too short
- **Solution:** Increased timeout to 30 seconds

---

## 🛠️ Technologies Used

| Technology     | Purpose                                |
|----------------|----------------------------------------|
| AWS EC2        | Virtual server instances               |
| AWS Lambda     | Serverless compute for automation      |
| AWS IAM        | Role-based access control              |
| AWS CloudWatch | Logging and monitoring                 |
| Python 3.12    | Lambda runtime language                |
| Boto3          | AWS SDK for Python                     |

---

## 🎯 Learning Outcomes

- Understanding of AWS Lambda serverless architecture
- Hands-on experience with Boto3 SDK
- EC2 instance management using tags
- IAM role creation and permission management
- CloudWatch log analysis
- Infrastructure automation concepts

---

## ⭐ Future Enhancements

- Add **CloudWatch EventBridge** rule for scheduled auto-execution
- Implement **SNS notifications** when instances are started/stopped
- Create **custom IAM policy** with least privilege access
- Add **error handling** and **retry logic**
- Implement **multi-region support**
- Add **Terraform/CloudFormation** templates for infrastructure as code

---

## 📎 Project Structure

```
aws-lambda-ec2-manager/
├── lambda_function.py     # Lambda function code
├── README.md              # Documentation (this file)
└── screenshots/           # Screenshots folder
    ├── ec2-dashboard.png
    ├── ec2-tags.png
    ├── iam-role.png
    ├── lambda-code.png
    ├── lambda-test.png
    ├── cloudwatch-logs.png
    └── ec2-after-lambda.png
```

---

## 👤 Author

**Sirajuddin Mohammed**
IT Engineer | DevOps | Cloud | SRE

---

## 📝 Important Notes

> ⚠️ **Region:** Ensure Lambda function region matches EC2 instance region.

> ⚠️ **Tags:** Tags are case-sensitive. Use exact values: `Action`, `Auto-Stop`, `Auto-Start`.

> ⚠️ **Cleanup:** Terminate EC2 instances after testing to avoid unnecessary AWS charges.

> ⚠️ **Security:** In production, replace `AmazonEC2FullAccess` with a custom least-privilege policy.

---

✅ **Project successfully demonstrates automated EC2 instance management using AWS Lambda and Boto3.**
