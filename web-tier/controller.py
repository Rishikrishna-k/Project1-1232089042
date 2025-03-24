# # import boto3
# # import time

# # # AWS configuration
# # REGION = "us-east-1"  # Change this to your AWS region
# # AMI_ID = "ami-0eb332e727a8fd19b"  # Replace with your actual AMI ID
# # INSTANCE_TYPE = "t2.micro"
# # SECURITY_GROUP = "sg-07774c4853a268796"  # Replace with your security group ID
# # KEY_NAME = "web-instance"  # Replace with your key pair name

# # # Define limits
# # MAX_INSTANCES = 15
# # QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/your-account-id/your-queue"  # Replace with actual SQS queue URL

# # # AWS clients
# # ec2 = boto3.client("ec2", region_name=REGION)
# # sqs = boto3.client("sqs", region_name=REGION)

# # def get_pending_requests(queue_url):
# #     """Check the number of pending requests in the SQS queue."""
# #     try:
# #         response = sqs.get_queue_attributes(
# #             QueueUrl=queue_url, AttributeNames=["ApproximateNumberOfMessages"]
# #         )
# #         pending_requests = int(response["Attributes"].get("ApproximateNumberOfMessages", 0))
# #         print(f"[DEBUG] Pending Requests in Queue: {pending_requests}")
# #         return pending_requests
# #     except Exception as e:
# #         print(f"[ERROR] Failed to fetch pending requests: {e}")
# #         return 0

# # def get_running_instances():
# #     """Get all running instances in the application tier."""
# #     try:
# #         response = ec2.describe_instances(Filters=[{
# #             "Name": "instance-state-name", "Values": ["running"]},
# #             {"Name": "tag:Role", "Values": ["ApplicationTier"]}])
# #         instances = [inst["InstanceId"] for res in response["Reservations"] for inst in res["Instances"]]
# #         print(f"[DEBUG] Running ApplicationTier Instances: {instances}")
# #         return instances
# #     except Exception as e:
# #         print(f"[ERROR] Failed to fetch running instances: {e}")
# #         return []

# # def get_stopped_instances():
# #     """Get all stopped instances in the application tier."""
# #     try:
# #         response = ec2.describe_instances(Filters=[{
# #             "Name": "instance-state-name", "Values": ["stopped"]},
# #             {"Name": "tag:Role", "Values": ["ApplicationTier"]}])
# #         instances = [inst["InstanceId"] for res in response["Reservations"] for inst in res["Instances"]]
# #         print(f"[DEBUG] Stopped ApplicationTier Instances: {instances}")
# #         return instances
# #     except Exception as e:
# #         print(f"[ERROR] Failed to fetch stopped instances: {e}")
# #         return []

# # def start_instance():
# #     """Start a stopped EC2 instance if available; otherwise, launch a new one."""
# #     stopped_instances = get_stopped_instances()

# #     if stopped_instances:
# #         instance_id = stopped_instances[0]  # Start the first stopped instance
# #         ec2.start_instances(InstanceIds=[instance_id])
# #         print(f"[INFO] Started stopped instance: {instance_id}")
# #         return instance_id
# #     elif len(get_running_instances()) < MAX_INSTANCES:
# #         return launch_new_instance()
# #     else:
# #         print("[WARNING] Cannot start more instances. Max limit reached.")
# #         return None

# # def launch_new_instance():
# #     """Launch a new EC2 instance if we haven't reached the max limit."""
# #     if len(get_running_instances()) >= MAX_INSTANCES:
# #         print("[WARNING] Cannot launch new instance. Max limit reached.")
# #         return None

# #     # Define the user data script to run backend.py on instance start
# #     user_data_script = '''#!/bin/bash
# #     cd /home/ec2-user/app-tier || exit 1
# #     python backend.py
# #     '''

# #     try:
# #         response = ec2.run_instances(
# #             ImageId=AMI_ID,
# #             InstanceType=INSTANCE_TYPE,
# #             MinCount=1,
# #             MaxCount=1,
# #             KeyName=KEY_NAME,
# #             SecurityGroupIds=[SECURITY_GROUP],
# #             TagSpecifications=[{"ResourceType": "instance", "Tags": [{"Key": "Role", "Value": "ApplicationTier"}]}],
# #             UserData=user_data_script,  # Pass the user data script here
# #             InstanceInitiatedShutdownBehavior='stop'  # Instances will stop instead of terminating when shutdown
# #         )
# #         instance_id = response["Instances"][0]["InstanceId"]
# #         print(f"[INFO] Launched new instance: {instance_id}")
# #         return instance_id
# #     except Exception as e:
# #         print(f"[ERROR] Failed to launch a new instance: {e}")
# #         return None

# # def stop_instance(instance_id):
# #     """Stop an idle EC2 instance."""
# #     if not instance_id:
# #         print("[ERROR] Invalid instance ID received. Skipping stop request.")
# #         return
# #     try:
# #         ec2.stop_instances(InstanceIds=[instance_id])
# #         print(f"[INFO] Stopped instance: {instance_id}")
# #     except Exception as e:
# #         print(f"[ERROR] Failed to stop instance {instance_id}: {e}")

# # def ensure_max_instances():
# #     """Ensure that there are always 15 stopped or running instances."""
# #     stopped_instances = get_stopped_instances()
# #     running_instances = get_running_instances()
# #     total_instances = len(stopped_instances) + len(running_instances)

# #     if total_instances < MAX_INSTANCES:
# #         print("[INFO] Launching new instance to ensure there are always 15 total instances.")
# #         launch_new_instance()

# # def autoscale():
# #     """Autoscaling function to manage instance count based on pending requests."""
# #     time.sleep(2)  # Allow AWS to update instance states
# #     pending_requests = get_pending_requests(QUEUE_URL)
# #     running_instances = get_running_instances()

# #     # If there are no pending requests, stop all running instances
# #     if pending_requests == 0:
# #         print("[INFO] No requests in queue. Stopping all running instances...")
# #         for instance_id in running_instances:
# #             stop_instance(instance_id)

# #     # If there are fewer pending requests than running instances, scale down (stop idle instances)
# #     elif pending_requests < len(running_instances):
# #         print("[INFO] Fewer requests than running instances. Stopping idle instances...")
# #         for instance_id in running_instances[pending_requests:]:
# #             stop_instance(instance_id)

# #     # If there are more pending requests than running instances, start new instances
# #     elif pending_requests > len(running_instances):
# #         print("[INFO] More requests than running instances, starting new instance...")
# #         start_instance()

# #     ensure_max_instances()  # Ensure there are always 15 instances (stopped or running)

# # if __name__ == "__main__":
# #     # Create 15 instances in the stopped state if not already created
# #     ensure_max_instances()

# #     # Start the autoscaling logic
# #     while True:
# #         autoscale()
# #         time.sleep(5)  # Run autoscaling check every 5 seconds


import time
import boto3
import threading

# AWS Configuration
REGION = "us-east-1"  # Change this to your AWS region
AMI_ID = "ami-01965da820df0f59d"  # Replace with your actual AMI ID
INSTANCE_TYPE = "t2.micro"
SECURITY_GROUP = "sg-07774c4853a268796"  # Replace with your security group ID
KEY_NAME = "web-instance"  # Replace with your key pair name

# Define limits
MAX_INSTANCES = 15
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/390844739554/1232089042-req-queue"  # Replace with actual SQS queue URL

# Initialize AWS Clients
client_sqs = boto3.client('sqs', region_name=REGION)
client_ec2 = boto3.client('ec2', region_name=REGION)
resource_ec2 = boto3.resource('ec2', region_name=REGION)

# Store EC2 instances in a dictionary
instances = {}

# Create an EC2 instance
def create_application_instance(instance_index):
    try:
        print(f"Attempting to create EC2 instance {instance_index}...")

        response = client_ec2.run_instances(
            ImageId=AMI_ID,
            InstanceType=INSTANCE_TYPE,
            KeyName=KEY_NAME,
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[SECURITY_GROUP],
            UserData="""#!/bin/bash
                        sudo -u ec2-user nohup /usr/bin/python3 /home/ec2-user/app-tier/backend.py > /dev/null 2>&1 &
                    """,
            TagSpecifications=[ 
                { 
                    'ResourceType': 'instance',
                    'Tags': [ 
                        {
                            'Key': 'Name',
                            'Value': f'app-tier-instance-{instance_index}'
                        }
                    ]
                }
            ]
        )

        # Retrieve instance ID and stop the instance immediately after creation
        instance_id = response['Instances'][0]['InstanceId']
        print(f"Instance {instance_index} created successfully with ID: {instance_id}")

        ec2_instance = resource_ec2.Instance(instance_id)
        ec2_instance.stop()  # Stop the instance immediately after creation
        print(f"Instance {instance_index} is stopped.")
        
        instances[instance_index] = instance_id

    except Exception as e:
        print(f"Error creating instance {instance_index}: {str(e)}")


# Start an EC2 instance
def start_application_instance(instance_index):
    try:
        print(f"Attempting to start EC2 instance {instance_index}...")
        instance_id = instances[instance_index]
        ec2_instance = resource_ec2.Instance(instance_id)
        ec2_instance.start()  # Start the instance
        print(f"Instance {instance_index} started successfully.")
    except Exception as e:
        print(f"Error starting instance {instance_index}: {str(e)}")


# Stop an EC2 instance
def stop_application_instance(instance_index):
    try:
        print(f"Attempting to stop EC2 instance {instance_index}...")
        instance_id = instances[instance_index]
        ec2_instance = resource_ec2.Instance(instance_id)
        ec2_instance.stop()  # Stop the instance
        print(f"Instance {instance_index} stopped successfully.")
    except Exception as e:
        print(f"Error stopping instance {instance_index}: {str(e)}")


# Check the number of messages in the request queue
def get_queue_message_count():
    try:
        print("Fetching number of messages in the queue...")
        response = client_sqs.get_queue_attributes(
            QueueUrl=QUEUE_URL,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        message_count = int(response['Attributes']['ApproximateNumberOfMessages'])
        print(f"Number of messages in the queue: {message_count}")
        return message_count
    except Exception as e:
        print(f"Error fetching message count: {str(e)}")
        return 0


# Scale out (add instances)
def scale_out(new_instances_count):
    print(f"Scaling out by {new_instances_count} instances...")
    current_instance_index = len(instances) + 1
    threads = []

    for i in range(current_instance_index, current_instance_index + new_instances_count):
        thread = threading.Thread(target=create_application_instance, args=(i,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()
    
    print("Scaling out completed.")


# Scale in (stop instances)
def scale_in(instances_to_stop):
    print(f"Scaling in by stopping {instances_to_stop} instances...")
    current_instance_count = len(instances)

    for i in range(current_instance_count, current_instance_count - instances_to_stop, -1):
        stop_application_instance(i)

    print("Scaling in completed.")


# Initialize the system with 15 instances
def init():
    print("Initializing EC2 instances...")

    # Fetch all instances with the name starting with 'app-tier-instance' and that are not terminated
    instances_in_ec2 = resource_ec2.instances.filter(
        Filters=[{'Name': 'tag:Name', 'Values': ['app-tier-instance-*']},
                 {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}]
    )
    
    # List of existing instance IDs
    existing_instance_ids = [instance.id for instance in instances_in_ec2]
    existing_instance_count = len(existing_instance_ids)
    
    print(f"Existing instances found (running or stopped): {existing_instance_count}")

    # Create new instances if there are fewer than 15
    if existing_instance_count < MAX_INSTANCES:
        instances_to_create = MAX_INSTANCES - existing_instance_count
        print(f"Creating {instances_to_create} new instances...")
        current_instance_index = existing_instance_count + 1
        threads = []

        for i in range(current_instance_index, current_instance_index + instances_to_create):
            thread = threading.Thread(target=create_application_instance, args=(i,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        print("Initialization completed with 15 instances.")
    else:
        print("Already have 15 instances. Initialization skipped.")



# Main logic for autoscaling
def auto_scaling_controller():
    while True:
        print("Checking for autoscaling conditions...")

        # Fetch the current number of messages in the queue
        message_count = get_queue_message_count()
        current_instance_count = len(instances)

        print(f"Queue Message Count: {message_count}, Current Instance Count: {current_instance_count}")

        # Scale out: If there are more messages than instances, we scale out
        if message_count > current_instance_count:
            instances_to_create = min(message_count - current_instance_count, MAX_INSTANCES - current_instance_count)
            if instances_to_create > 0:
                scale_out(instances_to_create)

        # Scale in: If there are fewer messages than instances, we scale in
        elif message_count < current_instance_count:
            instances_to_stop = current_instance_count - message_count
            if instances_to_stop > 0:
                scale_in(instances_to_stop)

        # Manage idle instances: If no messages, stop idle instances
        elif message_count == 0 and current_instance_count > 0:
            print("No messages in the queue. Stopping idle instances...")
            for i in range(current_instance_count, 0, -1):
                stop_application_instance(i)

        time.sleep(5)  # Delay before next check


if __name__ == "__main__":
    try:
        # Initialize instances at the start
        init()

        # Start the autoscaling controller
        print("Starting the autoscaling controller...")
        auto_scaling_controller()
    except KeyboardInterrupt:







        print("Autoscaling controller stopped.")
# import time
# import boto3
# import threading

# # AWS Configuration
# REGION = "us-east-1"
# AMI_ID = "ami-01965da820df0f59d"
# INSTANCE_TYPE = "t2.micro"
# SECURITY_GROUP = "sg-07774c4853a268796"
# KEY_NAME = "web-instance"
# MAX_INSTANCES = 15
# QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/390844739554/1232089042-req-queue"

# # AWS Clients
# client_sqs = boto3.client('sqs', region_name=REGION)
# client_ec2 = boto3.client('ec2', region_name=REGION)
# resource_ec2 = boto3.resource('ec2', region_name=REGION)

# # Store EC2 instances and their states in a dictionary
# instances_dict = {}

# # Get queue message count
# def get_queue_message_count():
#     try:
#         response = client_sqs.get_queue_attributes(
#             QueueUrl=QUEUE_URL,
#             AttributeNames=['ApproximateNumberOfMessages']
#         )
#         return int(response['Attributes']['ApproximateNumberOfMessages'])
#     except Exception as e:
#         print(f"Error fetching message count: {str(e)}")
#         return 0

# # Start a stopped instance and update its state in the dictionary
# def start_application_instance(instance_id):
#     try:
#         ec2_instance = resource_ec2.Instance(instance_id)
#         ec2_instance.start()
#         instances_dict[instance_id] = 'running'  # Update state to running
#         print(f"Instance {instance_id} started.")
#     except Exception as e:
#         print(f"Error starting instance {instance_id}: {str(e)}")

# # Stop an instance and update its state in the dictionary
# def stop_application_instance(instance_id):
#     try:
#         ec2_instance = resource_ec2.Instance(instance_id)
#         ec2_instance.stop()
#         instances_dict[instance_id] = 'stopped'  # Update state to stopped
#         print(f"Instance {instance_id} stopped.")
#     except Exception as e:
#         print(f"Error stopping instance {instance_id}: {str(e)}")

# # Get instances by their name and state
# def get_instances_by_state(state):
#     try:
#         instances = [
#             instance.id for instance in resource_ec2.instances.filter(
#                 Filters=[{'Name': 'tag:Name', 'Values': ['app-tier-instance-*']},
#                          {'Name': 'instance-state-name', 'Values': ['stopped']}
# ]
                
#             )
#             if instances_dict.get(instance.id) == state
#         ]
#         return instances
#     except Exception as e:
#         print(f"Error fetching instances in state {state}: {str(e)}")
#         return []

# # Scale out: Start stopped instances first, then create new if needed
# def scale_out(new_instances_count):
#     print(f"Scaling out by {new_instances_count} instances...")

#     stopped_instances = get_instances_by_state('stopped')

#     threads = []
    
#     # Start stopped instances first
#     for i in range(min(new_instances_count, len(stopped_instances))):
#         thread = threading.Thread(target=start_application_instance, args=(stopped_instances[i],))
#         thread.start()
#         threads.append(thread)
#         new_instances_count -= 1  # Reduce remaining count

#     # Wait for started instances to finish
#     for thread in threads:
#         thread.join()

#     # After scaling out, update the dictionary for started instances
#     for instance_id in stopped_instances[:new_instances_count]:
#         instances_dict[instance_id] = 'running'

#     print("Scaling out completed.")

# # Scale in: Stop instances and update the dictionary
# def scale_in(instances_to_stop):
#     print(f"Scaling in by stopping {instances_to_stop} instances...")

#     running_instances = get_instances_by_state('running')

#     for i in range(min(instances_to_stop, len(running_instances))):
#         stop_application_instance(running_instances[i])

#     print("Scaling in completed.")

# # Ensure all instances are stopped when there are no messages
# def stop_all_instances():
#     print("No messages in the queue. Stopping all instances...")
#     running_instances = get_instances_by_state('running')

#     for instance_id in running_instances:
#         stop_application_instance(instance_id)

#     print("All instances stopped.")

# # Initialize instances
# def init():
#     print("Initializing EC2 instances...")

#     all_instances = list(resource_ec2.instances.filter(
#         Filters=[{'Name': 'tag:Name', 'Values': ['app-tier-instance-*']},
#                  {'Name': 'instance-state-name', 'Values': ['stopped']}]
#     ))

#     for instance in all_instances:
#         # Initialize dictionary with instance IDs and their state
#         instances_dict[instance.id] = instance.state['Name']
#     print(instances_dict)

#     print(f"Found {len(instances_dict)} instances.")
#     print("Initialization complete.")

# # Auto-scaling controller
# def auto_scaling_controller():
#     while True:
#         print("Checking for autoscaling conditions...")

#         message_count = get_queue_message_count()
#         running_instances = get_instances_by_state('running')
#         current_instance_count = len(running_instances)

#         print(f"Queue Message Count: {message_count}, Running Instances: {current_instance_count}")

#         if message_count > current_instance_count:
#             instances_to_start = min(message_count - current_instance_count, MAX_INSTANCES - current_instance_count)
#             scale_out(instances_to_start)

#         elif message_count < current_instance_count:
#             instances_to_stop = current_instance_count - message_count
#             scale_in(instances_to_stop)

#         elif message_count == 0 and current_instance_count > 0:
#             stop_all_instances()

#         time.sleep(5)

# # Run the program
# if __name__ == "__main__":
#     try:
#         init()
#         print("Starting the autoscaling controller...")
#         auto_scaling_controller()
#     except KeyboardInterrupt:
#         print("Autoscaling controller stopped.")

# import time
# import boto3
# import threading

# # AWS Configuration
# REGION = "us-east-1"
# AMI_ID = "ami-01965da820df0f59d"
# INSTANCE_TYPE = "t2.micro"
# SECURITY_GROUP = "sg-07774c4853a268796"
# KEY_NAME = "web-instance"
# MAX_INSTANCES = 15
# QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/390844739554/1232089042-req-queue"

# # AWS Clients
# client_sqs = boto3.client('sqs', region_name=REGION)
# client_ec2 = boto3.client('ec2', region_name=REGION)
# resource_ec2 = boto3.resource('ec2', region_name=REGION)

# # Store EC2 instances and their states in a dictionary
# def get_queue_length():
#     attributes = client_sqs.get_queue_attributes(
#         QueueUrl=QUEUE_URL,
#         AttributeNames=['ApproximateNumberOfMessages']
#     )
#     return int(attributes['Attributes'].get('ApproximateNumberOfMessages', '0'))

# def fetch_instances():
#     return list(resource_ec2.instances.filter(
#         Filters=[
#             {'Name': 'tag:AppTier', 'Values': ['true']},
#             {'Name': 'instance-state-name', 'Values': ['running', 'pending']}
#         ]))

# def create_instance(instance_number):
#     print("Launching instance:", instance_number)
#     return resource_ec2.create_instances(
#         ImageId=AMI_ID,
#         MinCount=1,
#         MaxCount=1,
#         InstanceType='t2.micro',
#         KeyName=KEY_NAME,
#         TagSpecifications=[{
#             'ResourceType': 'instance',
#             'Tags': [
#                 {'Key': 'Name', 'Value': f'app-tier-instance-{instance_number}'},
#                 {'Key': 'AppTier', 'Value': 'true'}
#             ]
#         }],
#         UserData="""#!/bin/bash
#                 sudo -u ec2-user nohup /usr/bin/python3 /home/ec2-user/app-tier/backend.py > /dev/null 2>&1 &
#                 """
#     )

# def autoscale_instances(queue_count):
#     required_count = min(MAX_INSTANCES, queue_count)
#     if queue_count == 0 and required_count > 0:
#         required_count = 0
#     current_instances = fetch_instances()

#     if len(current_instances) < required_count:
#         more_required = required_count - len(current_instances)
#         for i in range(more_required):
#             create_instance(len(current_instances) + 1 + i)
#             print("Launched instance successfully")
#     elif len(current_instances) > required_count:
#         instances_to_terminate = []
#         for inst in current_instances[required_count:]:
#             instances_to_terminate.append(inst.id)
#         client_ec2.terminate_instances(InstanceIds=instances_to_terminate)
#         print(f"Terminated {len(instances_to_terminate)} instances.")

# if __name__ == "__main__":
#     while True:
#         autoscale_instances(get_queue_length())
#         time.sleep(1)

