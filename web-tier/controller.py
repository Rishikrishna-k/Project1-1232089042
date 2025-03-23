import boto3
import time

# AWS configuration
REGION = "us-east-1"  # Change this to your AWS region
AMI_ID = "ami-12345678"  # Replace with your actual AMI ID
INSTANCE_TYPE = "t2.micro"
SECURITY_GROUP = "sg-07774c4853a268796"  # Replace with your security group ID
KEY_NAME = "web-instance"  # Replace with your key pair name

# Define limits
MAX_INSTANCES = 15
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/your-account-id/your-queue"  # Replace with actual SQS queue URL

# AWS clients
ec2 = boto3.client("ec2", region_name=REGION)
sqs = boto3.client("sqs", region_name=REGION)


def get_pending_requests(queue_url):
    """Check the number of pending requests in the SQS queue."""
    try:
        response = sqs.get_queue_attributes(
            QueueUrl=queue_url, AttributeNames=["ApproximateNumberOfMessages"]
        )
        pending_requests = int(response["Attributes"].get("ApproximateNumberOfMessages", 0))
        print(f"[DEBUG] Pending Requests in Queue: {pending_requests}")
        return pending_requests
    except Exception as e:
        print(f"[ERROR] Failed to fetch pending requests: {e}")
        return 0


def get_running_instances():
    """Get all running and pending instances in the application tier."""
    try:
        response = ec2.describe_instances(Filters=[
            {"Name": "instance-state-name", "Values": ["running", "pending"]},
            {"Name": "tag:Role", "Values": ["ApplicationTier"]}
        ])
        instances = [inst["InstanceId"] for res in response["Reservations"] for inst in res["Instances"]]
        print(f"[DEBUG] Running ApplicationTier Instances: {instances}")
        return instances
    except Exception as e:
        print(f"[ERROR] Failed to fetch running instances: {e}")
        return []


def get_stopped_instances():
    """Get all stopped instances in the application tier."""
    try:
        response = ec2.describe_instances(Filters=[
            {"Name": "instance-state-name", "Values": ["stopped"]},
            {"Name": "tag:Role", "Values": ["ApplicationTier"]}
        ])
        instances = [inst["InstanceId"] for res in response["Reservations"] for inst in res["Instances"]]
        print(f"[DEBUG] Stopped ApplicationTier Instances: {instances}")
        return instances
    except Exception as e:
        print(f"[ERROR] Failed to fetch stopped instances: {e}")
        return []


def start_instance():
    """Start a stopped EC2 instance if available; otherwise, launch a new one."""
    stopped_instances = get_stopped_instances()
    
    if stopped_instances:
        instance_id = stopped_instances[0]  # Start the first stopped instance
        ec2.start_instances(InstanceIds=[instance_id])
        print(f"[INFO] Started stopped instance: {instance_id}")
        return instance_id
    elif len(get_running_instances()) < MAX_INSTANCES:
        return launch_new_instance()
    else:
        print("[WARNING] Cannot start more instances. Limit reached.")
        return None


def launch_new_instance():
    """Launch a new EC2 instance if we haven't reached the max limit."""
    if len(get_running_instances()) >= MAX_INSTANCES:
        print("[WARNING] Cannot launch new instance. Max limit reached.")
        return None

    try:
        response = ec2.run_instances(
            ImageId=AMI_ID,
            InstanceType=INSTANCE_TYPE,
            MinCount=1,
            MaxCount=1,
            KeyName=KEY_NAME,
            SecurityGroupIds=[SECURITY_GROUP],
            TagSpecifications=[{"ResourceType": "instance", "Tags": [{"Key": "Role", "Value": "ApplicationTier"}]}]
        )
        instance_id = response["Instances"][0]["InstanceId"]
        print(f"[INFO] Launched new instance: {instance_id}")
        return instance_id
    except Exception as e:
        print(f"[ERROR] Failed to launch a new instance: {e}")
        return None


def stop_instance(instance_id):
    """Stop an idle EC2 instance."""
    if not instance_id:
        print("[ERROR] Invalid instance ID received. Skipping stop request.")
        return
    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f"[INFO] Stopped instance: {instance_id}")
    except Exception as e:
        print(f"[ERROR] Failed to stop instance {instance_id}: {e}")


def autoscale():
    """Autoscaling function to manage instance count based on pending requests."""
    time.sleep(2)  # Allow AWS to update instance states
    pending_requests = get_pending_requests(QUEUE_URL)
    running_instances = get_running_instances()

    if pending_requests == 0 and running_instances:
        print("[INFO] No requests in queue. Stopping all instances...")
        for instance_id in running_instances:
            stop_instance(instance_id)
    elif pending_requests > len(running_instances):
        print("[INFO] More requests than running instances, starting new instance...")
        start_instance()
    elif pending_requests < len(running_instances):
        print("[INFO] Fewer requests than running instances, stopping an instance...")
        stop_instance(running_instances[-1])


if __name__ == "__main__":
    while True:
        autoscale()
        time.sleep(5)  # Run autoscaling check every 5 seconds
