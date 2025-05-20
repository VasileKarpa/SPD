FROM python:3.10-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential libssl-dev libffi-dev python3-dev libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

# copia só o requirements e instala
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# copia o código do backend
COPY . .

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
