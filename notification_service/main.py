# notification_service/main.py

import os
import json
import aio_pika
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI()

# DB connection (to query incomplete prescriptions if needed)
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

CONNECTION_STRING = (
    "Driver={ODBC Driver 18 for SQL Server};"
    f"Server=tcp:{DB_SERVER},1433;"
    f"Database={DB_NAME};"
    f"Uid={DB_USER};"
    f"Pwd={DB_PASSWORD};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

# RabbitMQ connection
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")

# We'll store incomplete prescriptions in memory for demonstration.
# In a real system, you'd store them in a DB or keep them updated by queries.
incomplete_prescriptions = []  # list of dicts: { "id": <int>, "timestamp": <datetime> }

async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            event = json.loads(message.body.decode())
            event_type = event.get("type")
            payload = event.get("payload", {})
            print(f"[NotificationService] Received event: {event_type}, payload: {payload}")

            if event_type == "PrescriptionStatusUpdated" and payload.get("status") == "INCOMPLETE":
                incomplete_prescriptions.append({
                    "prescription_group_id": payload["prescription_group_id"],
                    "timestamp": datetime.utcnow().isoformat(),  # Convert to string for JSON serialization
                })

        except Exception as e:
            print(f"Error processing message: {e}")

async def consume_prescription_events():
    """Continuously consume events from 'prescription_events' queue."""
    while True:
        try:
            # Connect to RabbitMQ with credentials and explicit port
            connection = await aio_pika.connect_robust(
                f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:5672/"
            )
            
            # Create channel
            channel = await connection.channel()
            
            # Declare queue
            queue = await channel.declare_queue(
                "prescription_events",
                durable=True
            )

            print("[NotificationService] Connected to RabbitMQ, waiting for messages...")
            
            # Start consuming messages
            await queue.consume(process_message)
            
            # Keep connection alive
            try:
                await asyncio.Future()  # run forever
            finally:
                await connection.close()

        except Exception as e:
            print(f"[NotificationService] Connection error: {e}")
            print("[NotificationService] Retrying in 5 seconds...")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    # Start the consumer in the background
    asyncio.create_task(consume_prescription_events())

@app.get("/notifications")
def get_notifications():
    return {
        "incomplete_prescriptions": incomplete_prescriptions,
        "count": len(incomplete_prescriptions)
    }

@app.get("/")
def health_check():
    return {"status": "Notification Service running"}
