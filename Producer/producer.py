from confluent_kafka import Producer
from dotenv import load_dotenv
import os
import time
import json
import uuid
import random

# Load environment variables from .env file
load_dotenv()

# Kafka Producer configuration using environment variables
conf = {
    'bootstrap.servers': os.getenv('BOOTSTRAP_SERVERS'),
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': os.getenv('SASL_USERNAME'),
    'sasl.password': os.getenv('SASL_PASSWORD')
}

# Create a Kafka producer
producer = Producer(conf)

# Function to create a complex dummy invoice
def create_dummy_invoice():
    num_items = random.randint(1, 5)
    items = []
    for _ in range(num_items):
        quantity = random.randint(1, 10)
        price = round(random.uniform(10.0, 500.0), 2)
        item = {
            "item_id": str(uuid.uuid4()),
            "description": f"Item {_ + 1}",
            "quantity": quantity,
            "price": price,
            "total": round(quantity * price, 2)
        }
        items.append(item)

    subtotal = sum(item["total"] for item in items)
    tax = round(subtotal * 0.08, 2)  # Assuming 8% tax
    total = round(subtotal + tax, 2)

    invoice = {
        "_id": str(uuid.uuid4()),
        "customer": {
            "name": f"Customer {uuid.uuid4().hex[:8]}",
            "email": f"customer{uuid.uuid4().hex[:5]}@example.com",
            "address": {
                "street": f"{random.randint(100, 9999)} Main St",
                "city": "Anytown",
                "state": "TX",
                "postal_code": f"{random.randint(10000, 99999)}"
            }
        },
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "timestamp": time.time()
    }
    return invoice

# Delivery callback for async message production
def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

# Produce 12 messages to Kafka at the same time
try:
    while True:
        invoices = [create_dummy_invoice() for _ in range(100)]
        for invoice in invoices:
            invoice_json = json.dumps(invoice)
            producer.produce('aws_demo', value=invoice_json, callback=delivery_report)
        producer.flush() 
        print("Produced 100 invoices concurrently")
        time.sleep(1)
except KeyboardInterrupt:
    print("Producer stopped.")
