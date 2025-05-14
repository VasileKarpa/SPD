import asyncio, os, json
from loguru import logger
from aioraft import RaftNode, MemoryLog, MemoryStorage

NODE_ID   = os.getenv("NODE_ID", "node1")
PEERS_RAW = os.getenv("PEERS", "node2,node3")        # “host,host2…”
RAFT_PORT = int(os.getenv("RAFT_PORT", 7000))

peers = [p for p in PEERS_RAW.split(",") if p and p != NODE_ID]

# ──────────────────────────────────────────────────────────────
# in-memory state; para persistir a log muda para RocksLog depois
log_store   = MemoryLog()
state_store = MemoryStorage()

node = RaftNode(
    id=NODE_ID,
    peers=peers,
    host=NODE_ID,          # container hostname = NODE_ID (compose faz isso)
    port=RAFT_PORT,
    log_store=log_store,
    state_store=state_store,
)

# chave-valor replicado (muito simples)
STATE = {}

async def _apply_entries():
    """escuta commits do Raft e aplica ao STATE local"""
    async for entry in node.commit_entries():
        cmd = json.loads(entry.data.decode())
        STATE[cmd["k"]] = cmd["v"]

async def start_cluster():
    await node.start()
    logger.info(f"Raft node {NODE_ID} listening on {RAFT_PORT}")
    asyncio.create_task(_apply_entries())

async def put(key: bytes, value: bytes):
    cmd = json.dumps({"k": key.decode(), "v": value.decode()}).encode()
    await node.append(cmd)      # envia ao líder; bloqueia até commit

def get(key: bytes):
    return STATE.get(key.decode()).encode() if key.decode() in STATE else None
