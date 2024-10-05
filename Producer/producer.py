import boto3
import json
import uuid
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the SQS client
sqs = boto3.client('sqs', region_name=os.getenv('AWS_REGION'))

# SQS queue URL from .env file
queue_url = os.getenv('SQS_QUEUE_URL')

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
        "timestamp": int(uuid.uuid1().time)
    }
    return invoice

def send_message():
    invoice = create_dummy_invoice()
    message_body = json.dumps(invoice)

    # Send the invoice message to the SQS queue
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=message_body
    )

    print(f"Message sent to SQS with ID: {response['MessageId']}")

if __name__ == "__main__":
    send_message()
