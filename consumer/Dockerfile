FROM python:3.10-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

# copia só as dependências do consumer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia todo o código do consumer
COPY . .

CMD ["python", "consumer.py"]
