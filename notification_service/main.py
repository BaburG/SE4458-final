# notification_service/main.py

import os
import time
import json
import pika
import pyodbc
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
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
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")

# We'll store incomplete prescriptions in memory for demonstration.
# In a real system, you'd store them in a DB or keep them updated by queries.
incomplete_prescriptions = []  # list of dicts: { "id": <int>, "timestamp": <datetime> }

def consume_prescription_events():
    """Continuously consume events from 'prescription_events' queue."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue='prescription_events', durable=True)

    def callback(ch, method, properties, body):
        try:
            event = json.loads(body.decode('utf-8'))
            event_type = event.get("type")
            payload = event.get("payload", {})
            print(f"[NotificationService] Received event: {event_type}, payload: {payload}")

            if event_type == "PrescriptionCreated":
                # For demonstration, do nothing here. Or you could track newly created prescription.
                pass

            elif event_type == "PrescriptionStatusUpdated":
                if payload.get("status") == "INCOMPLETE":
                    incomplete_prescriptions.append({
                        "prescription_group_id": payload["prescription_group_id"],
                        "timestamp": datetime.utcnow(),
                    })
                else:
                    # If it was completed, remove from incomplete if found
                    existing = [p for p in incomplete_prescriptions if p["prescription_group_id"] == payload["prescription_group_id"]]
                    for ex in existing:
                        incomplete_prescriptions.remove(ex)
            
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error processing event message: {e}")
            # Optionally, we could do a negative ack or requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue='prescription_events', on_message_callback=callback)
    print("[NotificationService] Waiting for messages from 'prescription_events'...")
    channel.start_consuming()

def send_daily_incomplete_report():
    """Called daily at 1:00 AM. Emails or logs the incomplete prescriptions."""
    print(f"[NotificationService] Running daily incomplete report at {datetime.now()}")

    # In a real scenario: group by pharmacy, send an actual email.
    # For demonstration, we just log them:
    if not incomplete_prescriptions:
        print("[NotificationService] No incomplete prescriptions to report today.")
        return

    print("[NotificationService] The following prescriptions are still incomplete:")
    for p in incomplete_prescriptions:
        print(f"  - ID: {p['prescription_group_id']} (marked incomplete at {p['timestamp']})")

    # Example: you could also re-check the DB to confirm if they are still incomplete

# APScheduler background scheduler
scheduler = BackgroundScheduler()
# Schedule daily at 01:00 
scheduler.add_job(send_daily_incomplete_report, 'cron', hour=1, minute=0)
scheduler.start()

# We'll run the consumer in a separate thread so it doesn't block.
import threading

consumer_thread = threading.Thread(target=consume_prescription_events, daemon=True)
consumer_thread.start()

@app.get("/")
def health_check():
    return {"status": "Notification Service running"}
