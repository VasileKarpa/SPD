FROM python:3.10-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libpq-dev \
      docker.io \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "scale_monitor.py"]
