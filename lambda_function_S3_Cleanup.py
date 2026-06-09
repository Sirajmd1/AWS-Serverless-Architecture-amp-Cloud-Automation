import boto3
from datetime import datetime, timezone, timedelta

def lambda_handler(event, context):

    # =============================================
    # CONFIGURATION
    # =============================================
    BUCKET_NAME = 's3-auto-cleanup-siraj'   # Change to your bucket name
    MAX_AGE_DAYS = 30                        # Delete files older than 30 days

    print(f"🪣 Bucket: {BUCKET_NAME}")
    print(f"📅 Max Age: {MAX_AGE_DAYS} days")
    print(f"⏰ Current Time: {datetime.now(timezone.utc)}")

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
        print(f"❌ Error accessing bucket: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }

    # Check if bucket has objects
    if 'Contents' not in response:
        print("ℹ️ Bucket is empty. Nothing to clean up.")
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

    print(f"📊 Total objects found: {total_objects}")
    print(f"📅 Cutoff date: {cutoff_date}")
    print("=" * 60)

    for obj in response['Contents']:
        file_key = obj['Key']
        last_modified = obj['LastModified']
        file_size = obj['Size']
        age_days = (datetime.now(timezone.utc) - last_modified).days

        print(f"📄 File: {file_key}")
        print(f"   Last Modified: {last_modified}")
        print(f"   Age: {age_days} days")
        print(f"   Size: {file_size} bytes")

        if last_modified < cutoff_date:
            # DELETE old file
            s3.delete_object(Bucket=BUCKET_NAME, Key=file_key)
            deleted_files.append(file_key)
            print(f"   🗑️ DELETED (older than {MAX_AGE_DAYS} days)")
        else:
            kept_files.append(file_key)
            print(f"   ✅ KEPT (within {MAX_AGE_DAYS} days)")

        print("-" * 40)

    # =============================================
    # SUMMARY
    # =============================================
    print("=" * 60)
    print(f"📊 CLEANUP SUMMARY")
    print(f"   Total Objects Scanned: {total_objects}")
    print(f"   Files Deleted: {len(deleted_files)}")
    print(f"   Files Kept: {len(kept_files)}")

    if deleted_files:
        print(f"   🗑️ Deleted Files: {deleted_files}")
    if kept_files:
        print(f"   ✅ Kept Files: {kept_files}")

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
