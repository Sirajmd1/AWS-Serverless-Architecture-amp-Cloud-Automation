# Assignment 5: Auto-Tagging EC2 Instances on Launch Using AWS Lambda and Boto3

## Objective
Automate the tagging of newly launched Amazon EC2 instances using **AWS Lambda** and **Boto3**. The solution automatically applies:
- the **current launch date**, and
- a **custom tag**

to every new EC2 instance for improved resource tracking, governance, and management.

---

## Solution Overview
This project uses an AWS Lambda function that is triggered automatically whenever an EC2 instance enters the **running** state. The Lambda function reads the instance ID from the event, generates the current date, and tags the instance using the AWS SDK for Python (**Boto3**).

### Workflow
1. A new EC2 instance is launched
2. Amazon EventBridge detects the EC2 instance state change event
3. EventBridge triggers the Lambda function
4. Lambda extracts the instance ID from the event payload
5. Lambda applies tags such as:
   - `LaunchDate=<current-date>`
   - `Environment=Dev`
6. Logs are written to **CloudWatch Logs** for verification

---

## AWS Services Used
- **Amazon EC2** – to launch and manage instances
- **AWS Lambda** – to run the automation logic
- **Amazon EventBridge (CloudWatch Events)** – to detect EC2 launch events and trigger Lambda
- **AWS IAM** – to provide permissions to Lambda
- **Amazon CloudWatch Logs** – to capture execution logs

---

## Prerequisites
Before starting, ensure you have:
- An active AWS account
- Permission to launch EC2 instances
- Access to **IAM**, **Lambda**, **EC2**, and **EventBridge**
- Basic familiarity with EC2 instance lifecycle states

---

## Architecture Flow
```text
EC2 Instance Launch
        ↓
Instance changes state to "running"
        ↓
EventBridge rule captures the event
        ↓
EventBridge triggers Lambda
        ↓
Lambda retrieves instance ID from event
        ↓
Lambda adds LaunchDate and custom tag
        ↓
CloudWatch Logs records success/failure
```

---

## Step 1: EC2 Setup
1. Open the **AWS Management Console**
2. Navigate to **EC2 Dashboard**
3. Ensure you have permission to launch EC2 instances
4. You can launch a test instance later to validate the automation

---

## Step 2: Create IAM Role for Lambda
1. Open the **IAM Console**
2. Navigate to **Roles** → **Create role**
3. Select **AWS service**
4. Choose **Lambda**
5. Click **Next**
6. Attach the policy:
   - `AmazonEC2FullAccess`
7. Enter the role name:
   ```text
   lambda-ec2-auto-tag-role
   ```
8. Click **Create role**

> **Note:** For assignment simplicity, `AmazonEC2FullAccess` is used. In production, use a least-privilege custom IAM policy.

---

## Step 3: Create Lambda Function
1. Open the **AWS Lambda Console**
2. Click **Create function**
3. Select **Author from scratch**
4. Configure the function:
   - **Function name:** `EC2-Auto-Tag-On-Launch`
   - **Runtime:** `Python 3.x`
5. Under **Permissions**:
   - Choose **Use an existing role**
   - Select `lambda-ec2-auto-tag-role`
6. Click **Create function**

---

## Step 4: Lambda Function Code
Replace the default function code with the script below.

```python
import boto3
from datetime import datetime

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    try:
        print("Received Event:", event)

        # Extract instance ID from EventBridge event
        instance_id = event['detail']['instance-id']

        # Generate current UTC date
        current_date = datetime.utcnow().strftime('%Y-%m-%d')

        # Define tags
        tags = [
            {'Key': 'LaunchDate', 'Value': current_date},
            {'Key': 'Environment', 'Value': 'Dev'}
        ]

        # Apply tags to EC2 instance
        ec2.create_tags(
            Resources=[instance_id],
            Tags=tags
        )

        print(f"Successfully tagged instance {instance_id} with LaunchDate={current_date} and Environment=Dev")

        return {
            'statusCode': 200,
            'body': f"Instance {instance_id} tagged successfully"
        }

    except Exception as e:
        print(f"Error tagging instance: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error tagging instance: {str(e)}"
        }
```

---

## Step 5: Deploy the Lambda Function
1. Paste the code into the Lambda code editor
2. Click **Deploy**
3. Confirm the deployment succeeds

---

## Step 6: Create EventBridge / CloudWatch Event Rule
This rule triggers the Lambda function whenever an EC2 instance enters the **running** state.

### Create the Rule
1. Open the **Amazon EventBridge Console**
2. Go to **Rules**
3. Click **Create rule**
4. Enter:
   - **Name:** `EC2-Launch-Auto-Tag-Rule`
   - **Description:** `Trigger Lambda when EC2 instance enters running state`
5. For **Event bus**, keep:
   - `default`
6. For **Rule type**, choose:
   - **Rule with an event pattern**

### Event Pattern
Use the following JSON event pattern:

```json
{
  "source": ["aws.ec2"],
  "detail-type": ["EC2 Instance State-change Notification"],
  "detail": {
    "state": ["running"]
  }
}
```

### Add Lambda Target
1. In the **Target** section, select:
   - **AWS service**
2. Choose:
   - **Lambda function**
3. Select:
   - `EC2-Auto-Tag-On-Launch`
4. Save and create the rule

### Why Use the `running` State?
Using the `running` state ensures:
- the instance is fully initialized
- the instance ID is available
- tags can be applied reliably

---

## Step 7: Testing the Solution
### Option A: Real Test with EC2 Launch
1. Open the **EC2 Console**
2. Launch a new EC2 instance
3. Wait for the instance to enter the **running** state
4. Open the instance details
5. Check the **Tags** tab

### Expected Tags
- `LaunchDate = YYYY-MM-DD`
- `Environment = Dev`

---

### Option B: Manual Lambda Test Event
You can also test the Lambda function manually using a sample EventBridge-style payload.

Use this test event:

```json
{
  "detail": {
    "instance-id": "i-1234567890abcdef0",
    "state": "running"
  }
}
```

> Replace `i-1234567890abcdef0` with a real EC2 instance ID from your AWS account.

---

## Step 8: Example Event Received by Lambda
When EventBridge triggers Lambda, the payload looks similar to this:

```json
{
  "version": "0",
  "id": "abcd1234-5678-90ab-cdef-111111111111",
  "detail-type": "EC2 Instance State-change Notification",
  "source": "aws.ec2",
  "account": "123456789012",
  "time": "2026-06-16T08:00:00Z",
  "region": "us-east-1",
  "resources": [
    "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"
  ],
  "detail": {
    "instance-id": "i-1234567890abcdef0",
    "state": "running"
  }
}
```

Lambda reads the instance ID using:

```python
event['detail']['instance-id']
```

---

## Step 9: Expected Output
### Lambda Response
```json
{
  "statusCode": 200,
  "body": "Instance i-1234567890abcdef0 tagged successfully"
}
```

### CloudWatch Logs Example
```text
Received Event: {...}
Successfully tagged instance i-1234567890abcdef0 with LaunchDate=2026-06-16 and Environment=Dev
```

---

## Step 10: Optional Improvement Using Environment Variables
Instead of hardcoding the custom tag, use Lambda environment variables.

### Suggested Variables
- `CUSTOM_TAG_KEY = Environment`
- `CUSTOM_TAG_VALUE = Dev`

### Updated Code
```python
import boto3
import os
from datetime import datetime

ec2 = boto3.client('ec2')
CUSTOM_TAG_KEY = os.environ.get('CUSTOM_TAG_KEY', 'Environment')
CUSTOM_TAG_VALUE = os.environ.get('CUSTOM_TAG_VALUE', 'Dev')

def lambda_handler(event, context):
    try:
        print("Received Event:", event)

        instance_id = event['detail']['instance-id']
        current_date = datetime.utcnow().strftime('%Y-%m-%d')

        tags = [
            {'Key': 'LaunchDate', 'Value': current_date},
            {'Key': CUSTOM_TAG_KEY, 'Value': CUSTOM_TAG_VALUE}
        ]

        ec2.create_tags(
            Resources=[instance_id],
            Tags=tags
        )

        print(f"Successfully tagged instance {instance_id} with LaunchDate={current_date} and {CUSTOM_TAG_KEY}={CUSTOM_TAG_VALUE}")

        return {
            'statusCode': 200,
            'body': f"Instance {instance_id} tagged successfully"
        }

    except Exception as e:
        print(f"Error tagging instance: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error tagging instance: {str(e)}"
        }
```

---

## Recommended Least-Privilege IAM Policy
For production use, replace `AmazonEC2FullAccess` with a narrower custom policy such as:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowTaggingInstances",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateTags",
        "ec2:DescribeInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Common Errors and Troubleshooting
### 1. Error: `'detail'`
**Cause:** The manual Lambda test event does not have the expected EventBridge structure.  
**Fix:** Use a test event that includes:

```json
{
  "detail": {
    "instance-id": "i-1234567890abcdef0",
    "state": "running"
  }
}
```

### 2. Lambda Not Triggered
**Cause:** EventBridge rule is misconfigured or disabled.  
**Fix:** Verify the event pattern, Lambda target, and rule status.

### 3. Access Denied
**Cause:** Lambda IAM role does not have permission to tag EC2 instances.  
**Fix:** Attach `AmazonEC2FullAccess` or grant `ec2:CreateTags`.

### 4. Instance Not Tagged
**Cause:** Wrong region, invalid instance ID, or incorrect event payload.  
**Fix:** Ensure EC2, Lambda, and EventBridge are in the same AWS region and use a valid instance ID.

---

## Sample Output
```text
Received Event: {'detail': {'instance-id': 'i-1234567890abcdef0', 'state': 'running'}}
Successfully tagged instance i-1234567890abcdef0 with LaunchDate=2026-06-16 and Environment=Dev
```

---

## Conclusion
This project demonstrates how to automate EC2 instance tagging at launch using **AWS Lambda**, **Amazon EventBridge**, and **Boto3**. The solution improves operational efficiency, supports resource management best practices, and ensures all launched instances are consistently tagged without manual intervention.

---

## Deliverables Included
- Lambda function using Python and Boto3
- Automatic tagging of EC2 instances on launch
- EventBridge rule for EC2 running-state events
- CloudWatch logging for monitoring and troubleshooting
- Custom tag and launch date tagging logic

---

## Author
**Name:** Sirajuddin Mohammed  
**Assignment:** Assignment 5 – Auto-Tagging EC2 Instances on Launch Using AWS Lambda and Boto3
