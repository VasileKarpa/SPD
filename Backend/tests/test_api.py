import pytest, httpx
from fastapi import FastAPI
from app.api import app

@pytest.fixture
def client():
    with httpx.Client(app=app, base_url="http://test") as c:
        yield c

def test_cycle(client):
    r = client.put("/", json={"key": "k", "value": "v"})
    assert r.status_code == 200
    assert client.get("/", params={"key": "k"}).json()["data"]["value"] == "v"
    assert client.delete("/", params={"key": "k"}).status_code == 200
    assert client.get("/", params={"key": "k"}).status_code == 404
