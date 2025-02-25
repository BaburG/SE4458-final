from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
import pyodbc
import random
from dotenv import load_dotenv
import os
import pika
import json
import requests


# Load environment variables
load_dotenv()

app = FastAPI()

# Database connection configuration
CONNECTION_STRING = (
    "Driver={ODBC Driver 18 for SQL Server};"
    f"Server=tcp:{os.getenv('DB_SERVER')},1433;"
    f"Database={os.getenv('DB_NAME')};"
    f"Uid={os.getenv('DB_USER')};"
    f"Pwd={os.getenv('DB_PASSWORD')};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "Connection Timeout=30;"
)

MEDS_SVC_HOST = os.getenv("MEDS_SVC_HOST", "http://localhost:8000")

def create_table():
    try:
        with pyodbc.connect(CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                # Create prescriptions table if it doesn't exist
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'prescriptions')
                    CREATE TABLE prescriptions (
                        id BIGINT PRIMARY KEY,
                        medicine_name VARCHAR(255),
                        quantity INT,
                        prescription_group_id BIGINT
                    )
                """)
                conn.commit()
    except Exception as e:
        print(f"Error creating table: {e}")
        raise HTTPException(status_code=500, detail="Database initialization failed")

# Generate a random 10-digit ID
def generate_prescription_id():
    return random.randint(1000000000, 9999999999)

class Prescription(BaseModel):
    data: List[Tuple[str, int]]

@app.on_event("startup")
async def startup_event():
    create_table()


def publish_event(event_type: str, payload: dict):
    """Publish a JSON event to the 'prescription_events' queue."""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
        )
        channel = connection.channel()
        channel.queue_declare(queue='prescription_events', durable=True)

        event_data = {
            "type": event_type,
            "payload": payload
        }
        message = json.dumps(event_data)
        channel.basic_publish(
            exchange='',
            routing_key='prescription_events',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            )
        )
        connection.close()
    except Exception as e:
        print(f"[WARNING] Failed to publish event {event_type}: {e}")


@app.post("/register-prescription")
async def register_prescription(prescription: Prescription):
    # Print the incoming request data
    print("Received prescription data:", prescription)
    
    try:
        prescription_group_id = generate_prescription_id()
        with pyodbc.connect(CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                for medicine_name, quantity in prescription.data:
                    medicine_id = generate_prescription_id()
                    cursor.execute("""
                        INSERT INTO prescriptions (id, medicine_name, quantity, prescription_group_id)
                        VALUES (?, ?, ?, ?)
                    """, (medicine_id, medicine_name, quantity, prescription_group_id))
                conn.commit()

        # Publish event after success:
        publish_event("PrescriptionCreated", {
            "prescription_group_id": prescription_group_id,
            "data": prescription.data
        })

        return {
            "status": "success",
            "id": prescription_group_id
        }

    except Exception as e:
        print(f"Error inserting prescription: {e}")
        raise HTTPException(status_code=500, detail="Failed to save prescription")

@app.get("/prescription/{prescription_group_id}")
async def get_prescription(prescription_group_id: int):
    try:
        with pyodbc.connect(CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT medicine_name, quantity 
                    FROM prescriptions 
                    WHERE prescription_group_id = ?
                """, (prescription_group_id,))
                
                results = cursor.fetchall()
                
                if not results:
                    raise HTTPException(status_code=404, detail="Prescription not found")
                
                prescription_data = [{"medicine_name": row[0], "quantity": row[1]} for row in results]
                
                return {
                    "status": "success",
                    "prescription_group_id": prescription_group_id,
                    "medications": prescription_data
                }
    
    except Exception as e:
        print(f"Error retrieving prescription: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve prescription")


@app.post("/prescription/submit/{prescription_group_id}")
async def submit_prescription_status(prescription_group_id: int):
    """
    Get the prescription by ID and check medicine existence against the medicine lookup service.
    Returns lists of filled (existing) and unfilled (non-existing) medicines.
    """
    try:
        with pyodbc.connect(CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT medicine_name
                    FROM prescriptions
                    WHERE prescription_group_id = ?
                """, (prescription_group_id,))
                
                results = cursor.fetchall()
                if not results:
                    raise HTTPException(status_code=404, detail="Prescription not found")

                all_medicines = [row[0] for row in results]
                
                lookup_response = requests.post(
                    f"{MEDS_SVC_HOST}/find-medicines",
                    json={"names": all_medicines}
                )
                
                if lookup_response.status_code != 200:
                    raise HTTPException(status_code=500, detail="Failed to verify medicines")
                
                lookup_data = lookup_response.json()
                
                # Use the lookup results to determine filled/unfilled
                filled_medicines = lookup_data["existing_medicines"]
                unfilled_medicines = lookup_data["non_existing_medicines"]
                
                status = "COMPLETED" if not unfilled_medicines else "INCOMPLETE"

                # Publish event about unfilled medicines
                if unfilled_medicines:
                    publish_event("UnfilledPrescription", {
                        "prescription_group_id": prescription_group_id,
                        "unfilled_medicines": unfilled_medicines
                    })

                return {
                    "status": status,
                    "prescription_group_id": prescription_group_id,
                    "filled_medicines": filled_medicines,
                    "unfilled_medicines": unfilled_medicines
                }

    except Exception as e:
        print(f"Error in submit_prescription_status: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit prescription status")