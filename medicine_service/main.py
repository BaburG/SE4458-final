from typing import Union, List
from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
import os
import random
import pandas as pd
from azure.cosmos import CosmosClient, PartitionKey
import uuid
import redis
import json
from pydantic import BaseModel

app = FastAPI()

# Cosmos DB settings
settings = {
    'host': os.environ.get('ACCOUNT_HOST', 'https://medicine-service-db.documents.azure.com:443/'),
    'master_key': os.environ.get('ACCOUNT_KEY', 'DnRFPpKpgEpM5EyDXT3WiTeskF5Ut3DQxk536SrT2RBStySOOeAmNXVbtvSOMxiLjgzLvGpridAjACDb8w7QfQ=='),
    'database_id': os.environ.get('COSMOS_DATABASE', 'ToDoList'),
    'container_id': os.environ.get('COSMOS_CONTAINER', 'Items'),
}

# Initialize Cosmos client
client = CosmosClient(settings['host'], settings['master_key'])

# Create database if it doesn't exist
try:
    database = client.create_database_if_not_exists(id=settings['database_id'])
except Exception as e:
    print(f"Error creating database: {str(e)}")
    database = client.get_database_client(settings['database_id'])

# Create container if it doesn't exist
try:
    container = database.create_container_if_not_exists(
        id=settings['container_id'],
        partition_key=PartitionKey(path="/id"),
        offer_throughput=400
    )
except Exception as e:
    print(f"Error creating container: {str(e)}")
    container = database.get_container_client(settings['container_id'])

# Initialize Redis client
redis_client = redis.Redis(
    host='redis-15622.c300.eu-central-1-1.ec2.redns.redis-cloud.com',
    port=15622,
    username='default',
    password='JPKOMUrVRoOHupFtTsF9WP1gRpUWF7Z2',
    decode_responses=True
)

async def save_to_cosmosdb(medicine_prices: dict):
    try:
        # Delete existing documents only if they exist
        query = "SELECT * FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        # Delete existing items if any
        for item in items:
            try:
                container.delete_item(item=item['id'], partition_key=item['id'])
            except Exception as delete_error:
                print(f"Error deleting item {item['id']}: {str(delete_error)}")
                # Continue with other items even if one fails
                continue
        
        # Create new document
        new_item = {
            'id': str(uuid.uuid4()),  # Required for Cosmos DB
            'medicines': medicine_prices,
            'type': 'medicine_list'  # Adding a type identifier
        }
        
        # Create the new item
        try:
            container.create_item(body=new_item)
            
            # Clear Redis cache as data has changed
            try:
                redis_client.flushdb()
            except redis.RedisError as e:
                print(f"Failed to clear Redis cache: {str(e)}")
                
            return True
            
        except Exception as create_error:
            print(f"Error creating new item: {str(create_error)}")
            return False
            
    except Exception as e:
        print(f"Cosmos DB Error: {str(e)}")
        return False

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/download-latest-xlsx")
def download_latest_xlsx():
    try:
        # Send GET request to the webpage
        url = "https://www.titck.gov.tr/dinamikmodul/43"
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the element using CSS selector
        xlsx_element = soup.select_one("#myTable > tbody > tr:nth-child(1) > td:nth-child(3) > div")
        
        if not xlsx_element:
            return {"error": "XLSX element not found"}
            
        # Find the link within the div
        xlsx_link = xlsx_element.find('a')
        if not xlsx_link or not xlsx_link.get('href'):
            return {"error": "XLSX link not found"}
            
        xlsx_url = xlsx_link['href']
        
        # Download the XLSX file
        file_response = requests.get(xlsx_url)
        file_response.raise_for_status()
        
        # Create downloads directory if it doesn't exist
        os.makedirs('downloads', exist_ok=True)
        
        # Extract filename from URL or use default name
        filename = xlsx_url.split('/')[-1] if '/' in xlsx_url else 'latest.xlsx'
        filepath = os.path.join('downloads', filename)
        
        # Save the file
        with open(filepath, 'wb') as f:
            f.write(file_response.content)
            
        return {
            "message": "File downloaded successfully",
            "filename": filename,
            "filepath": filepath
        }
        
    except requests.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


@app.get("/update-medicine-prices")
async def update_medicine_prices():
    try:
        # Download Excel file
        download_result = download_latest_xlsx()
        
        if "error" in download_result:
            return download_result
            
        filepath = download_result["filepath"]
        
        try:
            # Read both sheets from Excel
            medicine_names = []
            
            # Read Active Products sheet
            try:
                df_active = pd.read_excel(filepath, sheet_name="AKTİF ÜRÜNLER LİSTESİ", skiprows=3)
                active_names = df_active.iloc[:, 0].dropna().tolist()
                medicine_names.extend([name.strip() for name in active_names if isinstance(name, str)])
            except Exception as e:
                print(f"Error reading active products sheet: {str(e)}")
            
            # Read Passive Products sheet
            try:
                df_passive = pd.read_excel(filepath, sheet_name="PASİF ÜRÜNLER LİSTESİ", skiprows=3)
                passive_names = df_passive.iloc[:, 0].dropna().tolist()
                medicine_names.extend([name.strip() for name in passive_names if isinstance(name, str)])
            except Exception as e:
                print(f"Error reading passive products sheet: {str(e)}")
            
            if not medicine_names:
                return {"error": "No medicine names found in Excel file"}
            
            # Create prices dictionary
            medicine_prices = {
                name: random.randint(20, 70) 
                for name in medicine_names
            }
            
            # Save to Cosmos DB
            cosmos_save_success = await save_to_cosmosdb(medicine_prices)
            
            # Clear Redis cache
            try:
                redis_client.flushdb()
                cache_cleared = True
            except redis.RedisError as e:
                print(f"Failed to clear Redis cache: {str(e)}")
                cache_cleared = False
            
            return {
                "message": "Medicine prices updated successfully" + 
                          (" and saved to Cosmos DB" if cosmos_save_success else " but failed to save to Cosmos DB") +
                          (" and cache cleared" if cache_cleared else " but failed to clear cache"),
                "count": len(medicine_prices),
                "saved_to_cosmosdb": cosmos_save_success,
                "cache_cleared": cache_cleared
            }
            
        finally:
            # Clean up: Delete the downloaded file
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

@app.get("/find-medicine/{medicine_name}")
async def find_medicine(medicine_name: str):
    try:
        # First check Redis cache
        cached_result = redis_client.get(medicine_name)
        if cached_result is not None:
            return {
                "exists": json.loads(cached_result),
                "medicine_name": medicine_name,
                "source": "cache"
            }
        
        # If not in cache, query Cosmos DB
        query = "SELECT * FROM c WHERE IS_DEFINED(c.medicines)"
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        # Check if medicine exists in any document
        exists = any(
            medicine_name in item.get('medicines', {})
            for item in items
        )
        
        # Cache the result in Redis (with 1 hour expiration)
        redis_client.setex(
            medicine_name,
            3600,  # 1 hour in seconds
            json.dumps(exists)
        )
        
        return {
            "exists": exists,
            "medicine_name": medicine_name,
            "source": "database"
        }
        
    except redis.RedisError as e:
        print(f"Redis Error: {str(e)}")
        # If Redis fails, still return the database result
        return {
            "exists": exists,
            "medicine_name": medicine_name,
            "source": "database",
            "cache_error": str(e)
        }
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# Add this class for request validation
class MedicineListRequest(BaseModel):
    names: List[str]

@app.post("/find-medicines")
async def find_medicines(request: MedicineListRequest):
    try:
        results = {
            "existing_medicines": [],
            "non_existing_medicines": [],
            "cache_hits": [],
            "database_hits": [],
            "total_searched": len(request.names)
        }
        
        # First check Redis cache for all medicines
        cache_results = {}
        for medicine_name in request.names:
            cached_result = redis_client.get(medicine_name)
            if cached_result is not None:
                exists = json.loads(cached_result)
                cache_results[medicine_name] = exists
                results["cache_hits"].append(medicine_name)
                if exists:
                    results["existing_medicines"].append(medicine_name)
                else:
                    results["non_existing_medicines"].append(medicine_name)
        
        # Get remaining medicines that weren't in cache
        medicines_to_check = [
            name for name in request.names 
            if name not in cache_results
        ]
        
        if medicines_to_check:
            # Query Cosmos DB once for all medicines
            query = "SELECT * FROM c WHERE IS_DEFINED(c.medicines)"
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            # Get all medicines from the database
            all_medicines = {}
            for item in items:
                all_medicines.update(item.get('medicines', {}))
            
            # Check each medicine and update cache
            for medicine_name in medicines_to_check:
                exists = medicine_name in all_medicines
                results["database_hits"].append(medicine_name)
                
                if exists:
                    results["existing_medicines"].append(medicine_name)
                else:
                    results["non_existing_medicines"].append(medicine_name)
                
                # Cache the result
                try:
                    redis_client.setex(
                        medicine_name,
                        3600,  # 1 hour in seconds
                        json.dumps(exists)
                    )
                except redis.RedisError as e:
                    print(f"Failed to cache result for {medicine_name}: {str(e)}")
        
        # Add summary statistics
        results["summary"] = {
            "total_existing": len(results["existing_medicines"]),
            "total_non_existing": len(results["non_existing_medicines"]),
            "cache_hit_count": len(results["cache_hits"]),
            "database_hit_count": len(results["database_hits"])
        }
        
        return results
        
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}