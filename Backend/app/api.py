from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from prometheus_client import Counter, Gauge, generate_latest
from psycopg2.extras import RealDictCursor
from .storage import Storage

# ──────────────────────────────── Instâncias globais ────────────────────────────────
store = Storage()
app   = FastAPI()

REQ_COUNT = Counter("kv_requests_total", "Total de requisições", ["method"])
IS_LEADER = Gauge("is_leader",       "É líder? 1=yes 0=no")

# ─────────────────────────── Middleware de métricas ────────────────────────────────
@app.middleware("http")
async def _metrics_mw(request: Request, call_next):
    REQ_COUNT.labels(request.method).inc()
    return await call_next(request)

# ───────────────────────────────── End-points /api ─────────────────────────────────
class KVPair(BaseModel):
    key:   str
    value: str

@app.get("/api/health")
async def health():
    try:
        with store.conn.cursor() as cur:
            cur.execute("SELECT 1;")
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(500, f"Postgres error: {exc}")

@app.get("/api/metrics")
async def metrics():
    IS_LEADER.set(0)
    return generate_latest()

@app.put("/api")
async def put_value(kv: KVPair):
    store.put(kv.key.encode(), kv.value.encode())
    return {"status": "stored"}

@app.get("/api")
async def get_value(key: str):
    val = store.get(key.encode())
    if val is None:
        raise HTTPException(404, "key not found")
    return {"data": {"key": key, "value": val.decode()}}

@app.delete("/api")
async def delete_value(key: str):
    if store.get(key.encode()) is None:
        raise HTTPException(404, "key not found")
    store.delete(key.encode())
    return {"status": "deleted"}

# ─────────────────────────── Servir front-end estático ────────────────────────────

@app.get("/api/all")
async def list_all():
    try:
        with store.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT key, value FROM kv_store;")
            rows = cur.fetchall()  # lista de dicts: [{"key": "...", "value": "..."}, ...]
        return {"data": rows}
    except Exception as exc:
        raise HTTPException(500, f"Postgres error: {exc}")


app.mount(
    "/",
    StaticFiles(directory=str(Path(__file__).parent.parent / "frontend"), html=True),
    name="frontend",
)
