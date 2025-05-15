# backend/app/api.py
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from prometheus_client import Counter, Gauge, generate_latest

from .storage   import Storage
from .consensus import start_raft, put as raft_put, get as raft_get

# ──────────────────────────────── Instâncias globais ────────────────────────────────
DB_PATH = Path(__file__).parent.parent / "data"
DB_PATH.mkdir(parents=True, exist_ok=True)

store       = Storage(str(DB_PATH / "kv.rocks"))
app         = FastAPI()
REQ_COUNT   = Counter("kv_requests_total", "Total de requisições", ["method"])
IS_LEADER   = Gauge("is_leader", "É líder? 1=yes 0=no")

# ─────────────────────────────────── Modelos ────────────────────────────────────────
class KVPair(BaseModel):
    key: str
    value: str

# ─────────────────────────── Middleware de métricas ────────────────────────────────
@app.middleware("http")
async def _metrics_mw(request: Request, call_next):
    REQ_COUNT.labels(request.method).inc()
    return await call_next(request)

# ───────────────────────────────── End-points ───────────────────────────────────────
@app.get("/health")
async def health():
    try:
        _ = store.get(b"__ping__")
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(500, f"DB error: {exc}")

@app.get("/metrics")
async def metrics():
    # ainda não expomos o estado do líder → fica sempre 0
    IS_LEADER.set(0)
    return generate_latest()

@app.on_event("startup")
async def _startup():
    asyncio.create_task(start_raft())

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
