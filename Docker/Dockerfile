FROM python:3.11-slim

# 1) libs de sistema (build + MySQL client)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 2) dependências Python
WORKDIR /srv
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) códig​o
COPY backend/ .

# 4) arranque (Uvicorn)
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
