# Assignment 3: Monitor Unencrypted S3 Buckets Using AWS Lambda and Boto3

## Objective
To enhance AWS security by creating a Lambda function that detects S3 buckets without default server-side encryption enabled.

## Architecture Overview
- Amazon S3 → Stores buckets
- AWS Lambda → Scans buckets
- IAM Role → Permissions
- CloudWatch Logs → Output logs

## Prerequisites
- AWS Account
- Basic knowledge of AWS services

## S3 Setup
Create multiple buckets:
- Encrypted bucket (Enable default encryption)
- Unencrypted bucket (Do NOT enable encryption)

## IAM Role
Attach:
- AmazonS3ReadOnlyAccess
- AWSLambdaBasicExecutionRole

## Lambda Configuration
- Runtime: Python 3.x
- Role: LambdaS3EncryptionMonitorRole

## Lambda Code
```python
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

def lambda_handler(event, context):
    unencrypted_buckets = []

    response = s3.list_buckets()

    for bucket in response['Buckets']:
        name = bucket['Name']
        try:
            s3.get_bucket_encryption(Bucket=name)
            print(f"{name} is encrypted")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                print(f"{name} is NOT encrypted")
                unencrypted_buckets.append(name)

    print("Unencrypted buckets:", unencrypted_buckets)

    return {
        "statusCode": 200,
        "unencrypted_buckets": unencrypted_buckets
    }
```

## Execution
1. Deploy Lambda
2. Click Test
3. Use {}

## Output
Logs in CloudWatch:
/aws/lambda/MonitorUnencryptedS3Buckets

## Conclusion
This solution detects unencrypted S3 buckets using AWS Lambda and Boto3.

## Author
Sirajuddin Mohammed
