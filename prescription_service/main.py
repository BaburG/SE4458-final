from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
import pyodbc
import random
from dotenv import load_dotenv
import os

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
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

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

@app.post("/register-prescription")
async def register_prescription(prescription: Prescription):
    # Print the incoming request data
    print("Received prescription data:", prescription)
    
    try:
        # Generate a unique prescription group ID
        prescription_group_id = generate_prescription_id()
        
        with pyodbc.connect(CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                # Insert each medicine with its quantity
                for medicine_name, quantity in prescription.data:
                    medicine_id = generate_prescription_id()
                    cursor.execute("""
                        INSERT INTO prescriptions (id, medicine_name, quantity, prescription_group_id)
                        VALUES (?, ?, ?, ?)
                    """, (medicine_id, medicine_name, quantity, prescription_group_id))
                conn.commit()
        
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
