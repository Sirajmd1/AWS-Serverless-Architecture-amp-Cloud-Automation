import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

def lambda_handler(event, context):
    unencrypted_buckets = []

    try:
        response = s3.list_buckets()
        buckets = response.get('Buckets', [])

        print("Scanning S3 buckets for default server-side encryption...")

        for bucket in buckets:
            bucket_name = bucket['Name']

            try:
                s3.get_bucket_encryption(Bucket=bucket_name)
                print(f"Bucket '{bucket_name}' has server-side encryption enabled.")

            except ClientError as e:
                error_code = e.response['Error']['Code']

                if error_code == 'ServerSideEncryptionConfigurationNotFoundError':
                    print(f"Bucket '{bucket_name}' does NOT have server-side encryption enabled.")
                    unencrypted_buckets.append(bucket_name)
                else:
                    print(f"Error checking bucket '{bucket_name}': {str(e)}")

        print("----- Scan Complete -----")
        if unencrypted_buckets:
            print("Unencrypted buckets found:")
            for name in unencrypted_buckets:
                print(name)
        else:
            print("All buckets have default server-side encryption enabled.")

        return {
            "statusCode": 200,
            "unencrypted_buckets": unencrypted_buckets,
            "message": "S3 bucket encryption scan completed successfully"
        }

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "message": "Failed to scan S3 buckets",
            "error": str(e)
        }