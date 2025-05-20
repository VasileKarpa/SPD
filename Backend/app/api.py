# backend/app/api.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import os, json, redis, pika
from .storage import Storage
from typing import List, Dict

store = Storage()
app = FastAPI()

# Inicialização de conexões
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT"))
)

rabbit_conn = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST"),
        port=int(os.getenv("RABBITMQ_PORT"))
    )
)
channel = rabbit_conn.channel()
channel.queue_declare(queue='add_key', durable=True)
channel.queue_declare(queue='del_key', durable=True)

# Modelo de dados
class KVPair(BaseModel):
    key: str
    value: str

@app.get("/api")
async def get_value(key: str):
    # 1) Tenta no Redis
    cached = redis_client.get(key)
    if cached is not None:
        decoded = cached.decode()
        print(f"[GET] key={key!r} → {decoded!r} (fetched from Redis)")
        return {"data": {"key": key, "value": decoded}, "source": "redis"}

    # 2) Se não há cache, vai ao Postgres
    val = store.get(key.encode())
    if val is None:
        print(f"[GET] key={key!r} → NOT FOUND (Postgres)")
        raise HTTPException(status_code=404, detail="key not found")

    decoded = val.decode()
    # Popula o cache
    redis_client.set(key, decoded)
    print(f"[GET] key={key!r} → {decoded!r} (fetched from Postgres, then cached)")
    return {"data": {"key": key, "value": decoded}, "source": "postgres"}


@app.get("/api/all")
async def list_all() -> Dict[str, List[Dict[str,str]]]:
    # supondo que no Storage adicionaste um método .all()
    rows = store.all()   # devia devolver List[{"key":str, "value":str, "last_updated":datetime}, …]
    # podes filtrar só key/value:
    data = [{"key": r["key"], "value": r["value"]} for r in rows]
    return {"data": data}


@app.put("/api")
async def put_value(kv: KVPair):
    payload = json.dumps({
        "key_name": kv.key,
        "key_value": kv.value,
        "timestamp": datetime.utcnow().isoformat()
    })
    channel.basic_publish(
        exchange='',
        routing_key='add_key',
        body=payload,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    return {"status": "queued"}

@app.delete("/api")
async def delete_value(key: str):
    payload = json.dumps({
        "key_name": key,
        "timestamp": datetime.utcnow().isoformat()
    })
    channel.basic_publish(
        exchange='',
        routing_key='del_key',
        body=payload,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    return {"status": "queued"}

# Serve frontend estático
app.mount(
    "/",
    StaticFiles(directory=str(Path(__file__).parent.parent / "frontend"), html=True),
    name="frontend"
)
