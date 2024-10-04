from confluent_kafka import Consumer, KafkaException
from dotenv import load_dotenv
import os
import boto3
import json
import logging
from decimal import Decimal

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables (useful for local testing)
load_dotenv()

# DynamoDB configuration
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
table = dynamodb.Table('aws_demo')

# Kafka Consumer configuration using environment variables
conf = {
    'bootstrap.servers': os.getenv('BOOTSTRAP_SERVERS'),
    'group.id': os.getenv('KAFKA_GROUP_ID', 'aws_demo_group'),
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False,  # Disable auto-commit for manual control
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': os.getenv('SASL_USERNAME'),
    'sasl.password': os.getenv('SASL_PASSWORD')
}

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

# Function to consume and process messages from Kafka
def consume_messages():
    # Create a Kafka consumer
    consumer = Consumer(conf)
    
    # Subscribe to the topic to consume messages from all partitions
    consumer.subscribe([os.getenv('KAFKA_TOPIC', 'aws_demo')])

    try:
        while True:  # Continuous polling for messages
            # Poll Kafka for messages (batch of 10 in this case)
            messages = consumer.consume(num_messages=10, timeout=10.0)

            if not messages:
                logging.info("No messages received.")
                continue

            for msg in messages:
                if msg is None:
                    continue
                if msg.error():
                    raise KafkaException(msg.error())

                # Decode message and process
                invoice = json.loads(msg.value().decode('utf-8'))
                partition = msg.partition()
                logging.info(f"Received message from partition {partition}")

                # Store the invoice in DynamoDB
                store_invoice(invoice)

                # Manually commit the message offset after processing
                consumer.commit(msg)
                logging.info(f"Offset committed for partition {partition}")

    except KafkaException as e:
        logging.error(f"Kafka error: {e}")
    
    except Exception as e:
        logging.error(f"Error: {e}")
    
    finally:
        consumer.close()

# Lambda handler (for running in Lambda)
def lambda_handler(event, context):
    consume_messages()

# Manual entry point for local execution
if __name__ == "__main__":
    logging.info("Running locally...")
    consume_messages()
