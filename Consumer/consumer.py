import boto3
import json
import os
import time
import logging
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION'))

# DynamoDB table name from .env file
dynamodb_table_name = os.getenv('DYNAMODB_TABLE_NAME')

# Reference the DynamoDB table
table = dynamodb.Table(dynamodb_table_name)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configure logging for Lambda (CloudWatch) and Kubernetes (stdout)
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(format=log_format)

# Function to convert float to Decimal for DynamoDB (DynamoDB doesn't accept float)
def convert_to_decimal(item):
    if isinstance(item, list):
        return [convert_to_decimal(i) for i in item]
    elif isinstance(item, dict):
        return {k: convert_to_decimal(v) for k, v in item.items()}
    elif isinstance(item, float):
        return Decimal(str(item))
    return item

# Function to store invoice in DynamoDB
def store_invoice(invoice):
    invoice = convert_to_decimal(invoice)  # Convert any float values to Decimal
    try:
        table.put_item(Item=invoice)
        logger.info(f"Stored invoice with _id: {invoice['_id']} in DynamoDB")
    except Exception as e:
        logger.error(f"Failed to store invoice with _id: {invoice['_id']} - {str(e)}")

# Function to process SQS messages in Lambda
def process_sqs_event(event):
    # Each SQS event can contain multiple records (messages)
    for record in event['Records']:
        # Process each message
        body = json.loads(record['body'])
        logger.info(f"Processing message: {json.dumps(body, indent=4)}")
        
        # Store the invoice in DynamoDB
        store_invoice(body)
        
        logger.info("Message processed and stored in DynamoDB.")

# Continuous polling loop for Kubernetes or local
def continuous_polling():
    # Initialize the SQS client for local/Kubernetes usage
    sqs = boto3.client('sqs', region_name=os.getenv('AWS_REGION'))
    queue_url = os.getenv('SQS_QUEUE_URL')
    
    try:
        while True:
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )

            if 'Messages' in response:
                for message in response['Messages']:
                    # Process the message
                    body = json.loads(message['Body'])
                    
                    # Store the invoice in DynamoDB
                    store_invoice(body)
                    
                    # Delete the message after processing
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    logger.info("Message deleted from SQS")
            else:
                logger.info("No messages to process.")
            
            time.sleep(2)  # Polling interval
    
    except KeyboardInterrupt:
        logger.warning("Polling stopped by user (Ctrl+C). Exiting gracefully...")
    except Exception as e:
        logger.error(f"An error occurred during polling: {str(e)}")

# Lambda handler for AWS Lambda
def lambda_handler(event, context):
    # Process SQS event in Lambda
    logger.info("Lambda function triggered.")
    process_sqs_event(event)

# Local entry point for testing or Kubernetes
if __name__ == "__main__":
    logger.info("Starting continuous polling in local/Kubernetes environment...")
    continuous_polling()
