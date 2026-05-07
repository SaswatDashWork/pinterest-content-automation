from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_workflow(client: AsyncClient) -> None:
    payload = {"name": "Test WF", "command": "open google.com", "description": "smoke test"}
    resp = await client.post("/api/workflows/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test WF"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_workflows(client: AsyncClient) -> None:
    resp = await client.get("/api/workflows/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_execution_returns_pending(client: AsyncClient) -> None:
    payload = {"command": "take a screenshot of https://example.com"}
    resp = await client.post("/api/executions/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["command"] == payload["command"]


@pytest.mark.asyncio
async def test_list_executions(client: AsyncClient) -> None:
    resp = await client.get("/api/executions/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_automation(client: AsyncClient) -> None:
    payload = {
        "name": "Daily Sheet Sync",
        "command_template": "Sync {url} to Colab",
        "tags": ["sheets", "colab"],
    }
    resp = await client.post("/api/automations/", json=payload)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Daily Sheet Sync"


@pytest.mark.asyncio
async def test_get_nonexistent_workflow(client: AsyncClient) -> None:
    resp = await client.get("/api/workflows/99999")
    assert resp.status_code == 404
