import boto3
import json
import torch
import os
import sys
import traceback

# Add model directory to path
sys.path.append(os.path.abspath("CSE546-SPRING-2025-model"))
from face_recognition import face_match  # Import face_match directly from model.py

# AWS Configuration
ASU_ID = "1232089042"  # Replace with your ASU ID
REQ_QUEUE_URL = f"{ASU_ID}-req-queue"
RESP_QUEUE_URL = f"{ASU_ID}-resp-queue"
S3_INPUT_BUCKET = f"{ASU_ID}-in-bucket"
S3_OUTPUT_BUCKET = f"{ASU_ID}-out-bucket"

# AWS Clients
sqs = boto3.client("sqs", region_name="us-east-1")
s3 = boto3.client("s3")

DATA_PATH = os.path.join(os.path.dirname(__file__), "CSE546-SPRING-2025-model", "data.pt")

# Define your local images directory
LOCAL_IMAGES_DIR = r"C:\Users\rishi\Desktop\cloud computing\projectv 1 part 2\local images"

def download_image(image_key):
    """Download image from S3 input bucket."""
    local_image_path = os.path.join(LOCAL_IMAGES_DIR, os.path.basename(image_key))
    print(f"[DEBUG] Downloading image from S3: {image_key} -> {local_image_path}")
    
    try:
        s3.download_file(S3_INPUT_BUCKET, image_key, local_image_path)
        print(f"[DEBUG] Image downloaded successfully: {local_image_path}")
        return local_image_path
    except Exception as e:
        print(f"[ERROR] Failed to download image {image_key}: {e}")
        traceback.print_exc()
        return None


def upload_result(image_key, result):
    """Upload recognition result to S3 output bucket."""
    print(f"[DEBUG] Uploading result to S3: {image_key}.json")
    result_json = json.dumps({"image": image_key, "prediction": result})
    try:
        s3.put_object(Bucket=S3_OUTPUT_BUCKET, Key=f"{image_key}.json", Body=result_json)
        print(f"[DEBUG] Result uploaded successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to upload result for {image_key}: {e}")
        traceback.print_exc()

def send_response(image_key, result):
    """Send the recognition result to the response queue."""
    message_body = f"{image_key}:{result['name']}"
    print(f"[DEBUG] Sending response to SQS: {message_body}")
    try:
        sqs.send_message(QueueUrl=RESP_QUEUE_URL, MessageBody=message_body)
        print(f"[DEBUG] Response sent successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to send response for {image_key}: {e}")
        traceback.print_exc()

def process_request():
    """Process messages from the SQS request queue."""
    print("[INFO] Application tier is running and waiting for messages...")
    while True:
        try:
            print("[DEBUG] Polling SQS for messages...")
            response = sqs.receive_message(
                QueueUrl=REQ_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )

            if "Messages" not in response:
                print("[DEBUG] No messages received, retrying...")
                continue  # No messages, retry

            for message in response["Messages"]:
                receipt_handle = message["ReceiptHandle"]
                body = message["Body"]
                image_key = body.strip()

                print(f"[INFO] Processing image: {image_key}")

                # Download image from S3
                image_path = download_image(image_key)
                if image_path is None:
                    print(f"[ERROR] Skipping image {image_key} due to download failure.")
                    continue

                try:
                    # Perform face recognition
                    print(f"[DEBUG] Running face recognition on {image_path}")
                    name, confidence = face_match(image_path)
                    print(f"[DEBUG] Face recognition result: Name={name}, Confidence={confidence}")
                    
                    # Format result
                    result = {"name": name, "confidence": confidence}
                    print(result)
                    # Upload result to S3
                    upload_result(image_key, result)

                    # Send response to SQS
                    send_response(image_key, result)

                    # Delete processed message from SQS
                    print(f"[DEBUG] Deleting message from request queue: {image_key}")
                    sqs.delete_message(QueueUrl=REQ_QUEUE_URL, ReceiptHandle=receipt_handle)
                    print(f"[DEBUG] Message deleted successfully.")

                except Exception as e:
                    print(f"[ERROR] Error processing image {image_key}: {e}")
                    traceback.print_exc()
        
        except Exception as e:
            print(f"[ERROR] Unexpected error in process_request: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    process_request()
