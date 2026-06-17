import boto3
from datetime import datetime

# Initialize EC2 client
ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    try:
        # Retrieve instance ID from the event
        instance_id = event['detail']['instance-id']

        # Get current date
        current_date = datetime.utcnow().strftime('%Y-%m-%d')

        # Define tags
        tags = [
            {'Key': 'LaunchDate', 'Value': current_date},
            {'Key': 'Environment', 'Value': 'Dev'}
        ]

        # Create tags on the EC2 instance
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