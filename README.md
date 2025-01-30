# SE4458 Final Project

This repository demonstrates a microservices-based system for handling prescriptions, medicine lookups, and pharmacy interactions. It includes:

- **Doctor Frontend**: A React-based application for doctors to look up and create prescriptions.
- **Pharmacy Frontend**: A React+TypeScript application for pharmacies to retrieve and submit prescription details.
- **Medicine Service**: A FastAPI application that manages medicine names and prices (retrieved from a remote Excel source).
- **Prescription Service**: A FastAPI application that stores prescriptions in a database (SQL Server) and checks medicines against the Medicine Service.
- **Notification Service**: A FastAPI application that consumes events (via RabbitMQ) and stores incomplete prescription notifications in memory (for demonstration).

Everything is orchestrated via **Docker Compose**, with **Nginx** acting as a gateway/reverse proxy. **RabbitMQ** is used for asynchronous communication. 


---
## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Services Overview](#services-overview)
3. [Development and Local Setup](#development-and-local-setup)
   - [Prerequisites](#prerequisites)
   - [Environment Variables](#environment-variables)
   - [Quick Start](#quick-start)
   - [Verifying the Setup](#verifying-the-setup)
4. [Routes and APIs](#routes-and-apis)
   - [Medicine Service](#medicine-service)
   - [Prescription Service](#prescription-service)
   - [Notification Service](#notification-service)
   - [Doctor Frontend](#doctor-frontend)
   - [Pharmacy Frontend](#pharmacy-frontend)
5. [Production Considerations](#production-considerations)
6. [Project Structure](#project-structure)
7. [License](#license)


---
## High-Level Architecture

```
                            ┌────────────────┐
                            │ Doctor Frontend│
                            └────────┬───────┘
                                     │ (NGINX / :80 /doctor/)
                                     ▼
                               ┌─────────────┐
                               │   Gateway   │
                               │   (Nginx)   │
                               └────────┬────┘
                                     │
                          ┌──────────┴─────────┐
                          │                    │
                          ▼                    ▼
                 ┌─────────────────┐    ┌───────────────────┐
                 │Medicine Service │    │Prescription Service│
                 │ (FastAPI)       │    │ (FastAPI + SQL)    │
                 └──────────▲──────┘    └────────────┬───────┘
                            │                       │
                            │ (HTTP calls)          │ (HTTP calls)
                            │                       │
                            ▼                       ▼
                 ┌─────────────────┐    ┌────────────────────┐
                 │ Notification    │    │ Pharmacy Frontend   │
                 │ Service (FastAPI│    │ (React+TypeScript)  │
                 └────────┬────────┘    └────────────┬────────┘
                          │                         │ (NGINX / :80 /pharmacy/)
                          │ (RabbitMQ events)       ▼
                 ┌────────▼─────────────────────────────────┐
                 │                RabbitMQ                  │
                 └──────────────────────────────────────────┘
```

1. **Doctor Frontend** lets doctors verify if a patient exists, create prescriptions, and add medicines.
2. **Prescription Service** stores the prescription data in a SQL Server database. It also checks medicine availability via the **Medicine Service**.
3. **Medicine Service** retrieves a current list of medicines (from a Turkish Ministry of Health Excel file, for example) and stores them in Cosmos DB. It also caches queries in Redis.
4. **Notification Service** listens to events published by the **Prescription Service** (for incomplete prescriptions) and holds them for demonstration.
5. **Pharmacy Frontend** loads existing prescriptions and submits them (filling or partially filling the medicines).


---
## Services Overview

### 1. Doctor Frontend
- **Framework**: React (Vite-based).
- **Port (default)**: 5173 (accessible via [http://localhost:8080/doctor/](http://localhost:8080/doctor/) through Nginx).
- **Purpose**: Doctors can look up patient info, create prescriptions, and add medicines.

### 2. Pharmacy Frontend
- **Framework**: React + TypeScript (Vite-based).
- **Port (default)**: 5174 (accessible via [http://localhost:8080/pharmacy/](http://localhost:8080/pharmacy/) through Nginx).
- **Purpose**: Pharmacies can look up a prescription by ID and submit it, marking which medicines were successfully filled.

### 3. Medicine Service
- **Language**: Python (FastAPI).
- **Port**: 8000.
- **Purpose**: Manages a centralized list of medicines in Azure Cosmos DB; updates from an online Excel file. Provides endpoints to check or autocomplete medicine names. Uses Redis for caching.

### 4. Prescription Service
- **Language**: Python (FastAPI).
- **Port**: 8001 (mapped to host port 8001).
- **Purpose**: Stores prescription records in SQL Server (via pyodbc), checks medicine existence by calling the Medicine Service, and publishes events to RabbitMQ.

### 5. Notification Service
- **Language**: Python (FastAPI + AioPika).
- **Port**: Not exposed externally (but can be if needed).
- **Purpose**: Consumes RabbitMQ events for incomplete prescriptions. Exposes an endpoint to see them (`/notifications`).

### 6. Nginx Gateway
- **Image**: `nginx:latest`.
- **Port**: 8080 (host).
- **Purpose**: Acts as a reverse proxy for the two frontends and the `medicine_service` routes. Also sets up CORS, websockets, etc.


---
## Development and Local Setup

### Prerequisites
- **Docker** and **Docker Compose** installed on your machine.
- Optional: Local or remote credentials for Azure SQL, Cosmos DB, and Redis if you want to connect to actual cloud services. Otherwise, you can modify or remove those references for local testing.

### Environment Variables
Each service has an `.env.example` with the necessary environment variables. For local development, create `.env` files from these examples (or supply them via Docker Compose overrides).

Examples:

- **`medicine_service/.env.example`**:
  ```bash
  COSMOS_HOST=your_cosmos_host
  COSMOS_KEY=your_cosmos_key
  COSMOS_DATABASE=your_database_name
  COSMOS_CONTAINER=your_container_name

  REDIS_HOST=your_redis_host
  REDIS_PORT=your_redis_port
  REDIS_USERNAME=your_redis_username
  REDIS_PASSWORD=your_redis_password
  ```

- **`prescription_service/.env.example`**:
  ```bash
  DB_SERVER=your_server_name.database.windows.net
  DB_NAME=your_database_name
  DB_USER=your_username
  DB_PASSWORD=your_password
  ```

- **`compose.yaml`** also references environment variables for `rabbitmq`, `medicine_service`, `prescription_service`, etc.  
  For example:
  ```yaml
  rabbitmq:
    environment:
      RABBITMQ_DEFAULT_USER: "${RABBITMQ_USER}"
      RABBITMQ_DEFAULT_PASS: "${RABBITMQ_PASS}"
  ...
  ```
  Make sure to set them in a top-level `.env` or export them in your shell:
  ```bash
  RABBITMQ_USER=guest
  RABBITMQ_PASS=guest
  ```

### Quick Start

1. **Clone this repository**:
   ```bash
   git clone https://github.com/YourUsername/YourRepo.git
   cd YourRepo
   ```

2. **(Optional) Copy `.env.example` files** to `.env` in each service folder if you want to override defaults:
   ```bash
   cp ./medicine_service/.env.example ./medicine_service/.env
   cp ./prescription_service/.env.example ./prescription_service/.env
   # etc...
   ```

3. **Build and run all services**:
   ```bash
   docker compose up --build
   ```
   This will spin up:
   - **RabbitMQ** (ports 5672, 15672)
   - **Medicine Service** (port 8000)
   - **Prescription Service** (port 8001)
   - **Notification Service** (background, no port exposed by default)
   - **Doctor Frontend** (port 5173, served via Nginx on [http://localhost:8080/doctor/](http://localhost:8080/doctor/))
   - **Pharmacy Frontend** (port 5174, served via Nginx on [http://localhost:8080/pharmacy/](http://localhost:8080/pharmacy/))
   - **Nginx** (port 8080)

### Verifying the Setup

- Open [http://localhost:8080/doctor/](http://localhost:8080/doctor/) to see the **Doctor Frontend**.  
- Open [http://localhost:8080/pharmacy/](http://localhost:8080/pharmacy/) to see the **Pharmacy Frontend**.  
- Check RabbitMQ management UI at [http://localhost:15672/](http://localhost:15672/) (default user/pass: `guest/guest`), if you used the default env.  
- Inspect logs with `docker compose logs -f`.

If you have issues connecting to external services like Azure SQL, Cosmos DB, or Redis, confirm your environment variables and network permissions.


---
## Routes and APIs

### Medicine Service

**Base URL** (through Docker Compose) is `http://medicine_service:8000/` internally or [http://localhost:8080/api/](http://localhost:8080/api/) through Nginx with the path `/api/...`.

| Route                               | Method | Description                                                             |
|-------------------------------------|--------|-------------------------------------------------------------------------|
| `/`                                 | GET    | Health check. Returns `"Hello": "World"`.                              |
| `/download-latest-xlsx`             | GET    | Downloads the latest medicine Excel file (from a public website).       |
| `/update-medicine-prices`           | GET    | Reads the downloaded Excel, updates Cosmos DB with random price data.   |
| `/find-medicine/{medicine_name}`    | GET    | Checks if a single `medicine_name` exists in the DB. Uses Redis cache.  |
| `/find-medicines`                   | POST   | Body: `{"names": ["MedicineA", "MedicineB"]}`. Returns which exist.     |
| `/find-similar/{partial_name}`      | GET    | Autocompletes medicines that contain `partial_name` (case-insensitive). |

### Prescription Service

**Base URL**: `http://prescription_service:8000/` internally or (no direct Nginx route by default except from Docker Compose to the frontends).

| Route                                           | Method | Description                                                                             |
|-------------------------------------------------|--------|-----------------------------------------------------------------------------------------|
| `/register-prescription`                        | POST   | Body: `{"data": [["Medicine1", 2], ["Medicine2", 1]]}` Creates a prescription record.   |
| `/prescription/{prescription_group_id}`         | GET    | Retrieves a prescription’s details (list of medicines).                                |
| `/prescription/submit/{prescription_group_id}`  | POST   | Checks each medicine against the Medicine Service. Returns `filled/unfilled` arrays.   |

### Notification Service

**Base URL**: `http://notification_service:8000/` (not exposed externally unless you map a port).

| Route          | Method | Description                                                             |
|----------------|--------|-------------------------------------------------------------------------|
| `/`            | GET    | Health check. Returns `{"status": "Notification Service running"}`.     |
| `/notifications` | GET    | Returns a list of incomplete prescriptions that were consumed via RabbitMQ. |

### Doctor Frontend

**Local Dev URL**: [http://localhost:8080/doctor/](http://localhost:8080/doctor/)

Features:
- A simplified UI to:
  - "Verify" a patient via a mock API call.
  - Add medicines (auto-complete from the Medicine Service).
  - Submit a prescription to the Prescription Service (`/register-prescription`).

### Pharmacy Frontend

**Local Dev URL**: [http://localhost:8080/pharmacy/](http://localhost:8080/pharmacy/)

Features:
- Look up an existing prescription by ID.
- View the medicines.
- Submit it to mark which medicines are filled vs. unfilled (calls `/prescription/submit/{id}`).




---
## Project Structure

```
├── compose.yaml                # Docker Compose for everything
├── doctor_frontend/           # React-based Doctor UI
│   ├── Dockerfile
│   ├── src/...
│   └── ...
├── pharmacy_frontend/         # React+TS-based Pharmacy UI
│   ├── Dockerfile
│   ├── src/...
│   └── ...
├── medicine_service/          # FastAPI microservice (Cosmos + Redis)
│   ├── Dockerfile
│   ├── main.py
│   └── ...
├── prescription_service/      # FastAPI microservice (SQL + RabbitMQ)
│   ├── Dockerfile
│   ├── main.py
│   └── ...
├── notification_service/      # FastAPI microservice consuming RabbitMQ
│   ├── Dockerfile
│   ├── main.py
│   └── ...
├── nginx.conf                 # Nginx gateway config
└── ...
```



**Enjoy building and exploring this microservices architecture!** If you encounter any issues or have suggestions, feel free to open an issue or contribute.
