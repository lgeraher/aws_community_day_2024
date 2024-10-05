import boto3
import json
import os
import time
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the SQS client and DynamoDB client
sqs = boto3.client('sqs', region_name=os.getenv('AWS_REGION'))
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION'))

# SQS queue URL and DynamoDB table name from .env file
queue_url = os.getenv('SQS_QUEUE_URL')
dynamodb_table_name = os.getenv('DYNAMODB_TABLE_NAME')  # Get table name from env

# Reference the DynamoDB table
table = dynamodb.Table(dynamodb_table_name)

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
    table.put_item(Item=invoice)
    print(f"Stored invoice with _id: {invoice['_id']} in DynamoDB")

# Function to receive and process messages from SQS
def receive_message():
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )

    if 'Messages' in response:
        for message in response['Messages']:
            # Process the message
            body = json.loads(message['Body'])
            print(f"Received message: {json.dumps(body, indent=4)}")
            
            # Store the invoice in DynamoDB
            store_invoice(body)
            
            # Delete the message after processing
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
            print("Message deleted from SQS")
    else:
        print("No messages to process.")

# Continuous polling loop for Kubernetes or local
def continuous_polling():
    try:
        while True:
            receive_message()
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nPolling stopped by user (Ctrl+C). Exiting gracefully...")

# Lambda handler for AWS Lambda
def lambda_handler(event, context):
    receive_message()

# Local entry point for testing
if __name__ == "__main__":
    continuous_polling()
