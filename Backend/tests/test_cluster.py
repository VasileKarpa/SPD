import asyncio, httpx, pytest

BASES = ["http://localhost:8001", "http://localhost:8002", "http://localhost:8003"]

@pytest.mark.asyncio
async def test_quorum_cycle():
    async with httpx.AsyncClient() as c:
        # escreve num nó aleatório
        r = await c.put(f"{BASES[0]}/", json={"key": "x", "value": "1"})
        assert r.status_code == 200

        # lê noutro
        r = await c.get(f"{BASES[1]}/", params={"key": "x"})
        assert r.json()["data"]["value"] == "1"
