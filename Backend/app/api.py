# backend/app/api.py
import os
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from prometheus_client import Counter, Gauge, generate_latest
from .consensus import start_cluster, put as raft_put, get as raft_get

from .storage import Storage
from .consensus import start_raft
from raftos import get_leader

# ──────────────────────────────────────────────────────────────
# 1. Instâncias globais
# ──────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).parent.parent / "data"
DB_PATH.mkdir(parents=True, exist_ok=True)

store = Storage(str(DB_PATH / "kv.rocks"))
app = FastAPI(title="Key-Value Store", version="0.1.0")

# Prometheus métricas
REQ_COUNT = Counter("kv_requests_total", "Total de requisições", ["method"])
IS_LEADER = Gauge("is_leader", "É líder? 1=yes 0=no")

# ──────────────────────────────────────────────────────────────
# 2. Modelos Pydantic
# ──────────────────────────────────────────────────────────────
class KVPair(BaseModel):
    key: str
    value: str

# ──────────────────────────────────────────────────────────────
# 3. Middleware de métricas
# ──────────────────────────────────────────────────────────────
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    REQ_COUNT.labels(request.method).inc()
    return await call_next(request)

# ──────────────────────────────────────────────────────────────
# 4. Endpoints
# ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Verifica se o RocksDB está acessível."""
    try:
        _ = store.get(b"__ping__")      # operação rápida
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(500, f"DB error: {exc}")

@app.get("/metrics")
async def metrics():
    """Exposição Prometheus em texto puro."""
    leader = await get_leader()
    is_leader = leader and leader[0] == os.getenv("NODE_ID", "node1")
    IS_LEADER.set(1 if is_leader else 0)
    return generate_latest()

@app.on_event("startup")
async def _startup():
    asyncio.create_task(start_cluster())

@app.put("/")
async def put_value(kv: KVPair):
    await raft_put(kv.key.encode(), kv.value.encode())
    return {"status": "stored"}

@app.get("/")
async def get_value(key: str):
    value = raft_get(key.encode())
    if value is None:
        raise HTTPException(404, "key not found")
    return {"data": {"key": key, "value": value.decode()}}

@app.delete("/")
async def delete_value(key: str):
    if store.get(key.encode()) is None:
        raise HTTPException(404, "key not found")
    store.delete(key.encode())
    return {"status": "deleted"}

