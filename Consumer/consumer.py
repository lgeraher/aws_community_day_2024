from confluent_kafka import Consumer, KafkaException
from dotenv import load_dotenv
import os
import boto3
import json
import logging
from decimal import Decimal

# Load environment variables from .env file
load_dotenv()

# DynamoDB configuration
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('aws_demo')

# Kafka Consumer configuration using environment variables
conf = {
    'bootstrap.servers': os.getenv('BOOTSTRAP_SERVERS'),
    'group.id': 'aws_demo_group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False,  # Disable auto-commit
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': os.getenv('SASL_USERNAME'),
    'sasl.password': os.getenv('SASL_PASSWORD')
}

# Create a Kafka consumer
consumer = Consumer(conf)

# Subscribe to the topic to consume messages from all partitions
consumer.subscribe(['aws_demo'])

# Set up logging
logging.basicConfig(level=logging.INFO)

# Function to convert floats to Decimals for DynamoDB
def convert_to_decimal(item):
    if isinstance(item, list):
        return [convert_to_decimal(i) for i in item]
    elif isinstance(item, dict):
        return {k: convert_to_decimal(v) for k, v in item.items()}
    elif isinstance(item, float):
        return Decimal(str(item))  # Convert float to Decimal
    return item

# Function to store invoice in DynamoDB
def store_invoice(invoice):
    invoice = convert_to_decimal(invoice)
    table.put_item(Item=invoice)
    logging.info(f"Stored invoice with _id: {invoice['_id']}")

# Consume messages from Kafka from all partitions
try:
    while True:
        msg = consumer.poll(timeout=1.0)

        if msg is None:
            continue
        if msg.error():
            raise KafkaException(msg.error())

        invoice = json.loads(msg.value().decode('utf-8'))
        partition = msg.partition()

        logging.info(f"Received message from partition {partition}")

        # Store the invoice in DynamoDB
        store_invoice(invoice)

        # Manually commit the message offset after processing
        consumer.commit(msg)
        logging.info(f"Offset committed for partition {partition}")

except KeyboardInterrupt:
    logging.info("Consumer stopped.")
finally:
    consumer.close()
