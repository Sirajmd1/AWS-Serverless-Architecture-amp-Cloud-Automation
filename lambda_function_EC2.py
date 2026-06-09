import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name='ap-south-1')  # Change region if needed

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
        print(f"✅ Stopping instances: {stop_instances}")
    else:
        print("ℹ️ No running instances found with Auto-Stop tag.")

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
        print(f"✅ Starting instances: {start_instances}")
    else:
        print("ℹ️ No stopped instances found with Auto-Start tag.")

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
