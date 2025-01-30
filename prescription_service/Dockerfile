# prescription_service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 1) Basic dependencies
RUN apt-get update && apt-get install -y \
    curl apt-transport-https gnupg2 \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# 2) Add Microsoft repo & GPG key (for Debian 11 / bullseye)
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# 3) Install msodbcsql18
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Then continue installing python dependencies:
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
