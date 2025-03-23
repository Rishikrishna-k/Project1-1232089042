from fastapi import FastAPI, File, UploadFile
import boto3
import asyncio
import os
import logging
import uuid

# Debugging - Logging Configuration
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# AWS Configuration (Replace with your actual AWS credentials or use IAM roles)
AWS_REGION = "us-east-1"
ASU_ID = "1232089042"  # Replace with your ASU ID

S3_BUCKET_NAME = f"{ASU_ID}-in-bucket"
SQS_REQUEST_QUEUE = f"{ASU_ID}-req-queue"
SQS_RESPONSE_QUEUE = f"{ASU_ID}-resp-queue"

# AWS Clients
s3 = boto3.client("s3", region_name=AWS_REGION)
sqs = boto3.client("sqs", region_name=AWS_REGION)

# Get SQS Queue URLs
sqs_req_url = sqs.get_queue_url(QueueName=SQS_REQUEST_QUEUE)["QueueUrl"]
sqs_resp_url = sqs.get_queue_url(QueueName=SQS_RESPONSE_QUEUE)["QueueUrl"]

# Initialize FastAPI
app = FastAPI()

import asyncio

MAX_WAIT_TIME = 30  # Maximum time to wait for a response (in seconds)

@app.post("/")
async def upload_file(inputFile: UploadFile = File(...)):
    try:
        logging.info(f"Received file: {inputFile.filename}")

        file_key = f"{uuid.uuid4()}_{inputFile.filename}"
        s3.upload_fileobj(inputFile.file, S3_BUCKET_NAME, file_key)
        sqs.send_message(QueueUrl=sqs_req_url, MessageBody=file_key)

        logging.info(f"File {file_key} uploaded and request sent to SQS.")

        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < MAX_WAIT_TIME:
            response = sqs.receive_message(QueueUrl=sqs_resp_url, MaxNumberOfMessages=1, WaitTimeSeconds=5)

            if "Messages" in response:
                for message in response["Messages"]:
                    body = message["Body"]
                    sqs.delete_message(QueueUrl=sqs_resp_url, ReceiptHandle=message["ReceiptHandle"])
                    logging.info(f"Received response: {body}")
                    return { "result": body }

            await asyncio.sleep(2)  # Reduce polling intensity

        return {"error": "Timeout: No response received from SQS within limit"}

    except Exception as e:
        logging.error(f"Error processing file: {e}")
        return {"error": str(e)}
