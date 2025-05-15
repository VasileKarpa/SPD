# app/consensus.py  – compatível com aioraft-ng 0.1.5
import asyncio, json, os
from loguru import logger

from aioraft import Raft
from aioraft.server import GrpcRaftServer
from aioraft.client import GrpcRaftClient

# ─────────────── Config do nó ───────────────
NODE_ID   = os.getenv("NODE_ID", "node1")
RAFT_PORT = int(os.getenv("RAFT_PORT", 7000))
PEERS     = [p for p in os.getenv("PEERS", "node2,node3").split(",")
             if p and p != NODE_ID]          # ex.: ["node2", "node3"]

# 1) lista de nós conhecida pelo algoritmo
CONFIG = [NODE_ID, *PEERS]                  # Iterable[RaftId]

# 2) transporte gRPC (não recebe host/porta nesta versão)
server = GrpcRaftServer()
client = GrpcRaftClient()

# 3) instância do motor Raft
node = Raft(
    id_           = NODE_ID,
    server        = server,
    client        = client,
    configuration = CONFIG,
)

# ─────────────── Estado chave-valor replicado ───────────────
STATE: dict[str, str] = {}

async def _apply_commits() -> None:
    """Aplica (locais) as entradas que ficaram *committed*."""
    async for entry in node.commit_entries():      # API 0.1.5
        cmd = json.loads(entry.data.decode())
        STATE[cmd["k"]] = cmd["v"]

# ─────────────── API chamada pelo FastAPI ───────────────
async def start_raft() -> None:
    """
    Arranca o servidor gRPC e começa a ouvir pedidos Raft.
    server.serve() não bloqueia – podemos lançar o apply_commits a seguir.
    """
    await server.start(NODE_ID, RAFT_PORT, node)
    logger.info(f"Raft {NODE_ID} a ouvir em {NODE_ID}:{RAFT_PORT}")
    asyncio.create_task(_apply_commits())

async def put(key: bytes, value: bytes) -> None:
    """Escreve (k,v) e só devolve após commit em maioria."""
    cmd = json.dumps({"k": key.decode(), "v": value.decode()}).encode()
    await node.propose(cmd)

def get(key: bytes) -> bytes | None:
    """Lê do estado local (já consistente via _apply_commits)."""
    val = STATE.get(key.decode())
    return val.encode() if val is not None else None
