# Backend/app/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
from .storage import Storage

DB_PATH = Path(__file__).parent.parent / "data"        # Backend/data/
DB_PATH.mkdir(parents=True, exist_ok=True)

store = Storage(str(DB_PATH / "kv.rocks"))
app = FastAPI(title="Key-Value Store", version="0.1.0")

class KVPair(BaseModel):
    key: str
    value: str

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def get_value(key: str):
    value = store.get(key.encode())
    if value is None:
        raise HTTPException(status_code=404, detail="key not found")
    return {"data": {"key": key, "value": value.decode()}}

@app.put("/")
async def put_value(kv: KVPair):
    store.put(kv.key.encode(), kv.value.encode())
    return {"status": "stored"}

@app.delete("/")
async def delete_value(key: str):
    if store.get(key.encode()) is None:
        raise HTTPException(status_code=404, detail="key not found")
    store.delete(key.encode())
    return {"status": "deleted"}
