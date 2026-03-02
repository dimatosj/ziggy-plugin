"""Tests for Ziggy MCP server tools."""
import json
import pytest
import tempfile
from pathlib import Path
import os


@pytest.fixture(autouse=True)
def test_data_dir(tmp_path):
    """Set ZIGGY_DATA_DIR to temp dir and reset server singletons for each test."""
    os.environ["ZIGGY_DATA_DIR"] = str(tmp_path)
    import ziggy_server
    # Reset singletons between tests
    ziggy_server._data_dir = None
    ziggy_server._task_service = None
    ziggy_server._foundation_service = None
    ziggy_server._entity_service = None
    ziggy_server._review_service = None
    ziggy_server._orchestrator = None
    yield tmp_path


class TestSetup:
    @pytest.mark.asyncio
    async def test_setup_creates_directory(self, test_data_dir):
        from ziggy_server import setup
        result = await setup(user_name="TestUser")
        result_data = json.loads(result)
        assert result_data["status"] == "initialized"
        assert (test_data_dir / "config.json").exists()

    @pytest.mark.asyncio
    async def test_tools_fail_before_setup(self, test_data_dir):
        from ziggy_server import analyze
        result = await analyze(text="buy milk")
        data = json.loads(result)
        assert data["code"] == "NOT_INITIALIZED"


class TestCapture:
    @pytest.mark.asyncio
    async def test_analyze_simple_task(self, test_data_dir):
        from ziggy_server import setup, analyze
        await setup(user_name="TestUser")
        result = await analyze(text="buy milk")
        data = json.loads(result)
        assert data["is_clear_task"] is True
        assert data["entity_detection"]["type"] == "task"

    @pytest.mark.asyncio
    async def test_store_task(self, test_data_dir):
        from ziggy_server import setup, store_task
        await setup(user_name="TestUser")
        result = await store_task(
            title="buy eggs",
            analysis=json.dumps({"entity_type": "task", "priority": {"level": "HIGH"}}),
        )
        data = json.loads(result)
        assert data["title"] == "buy eggs"
        assert data["status"] == "inbox"


class TestFoundation:
    @pytest.mark.asyncio
    async def test_update_and_get_foundation(self, test_data_dir):
        from ziggy_server import setup, update_foundation, get_foundation
        await setup(user_name="TestUser")
        await update_foundation(pillar="reality", content="# Reality\n\nTest content")
        result = await get_foundation()
        data = json.loads(result)
        assert "reality" in data
        assert "Test content" in data["reality"]
