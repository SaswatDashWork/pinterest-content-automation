from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tools.base_tool import BaseTool, ToolResult
from tools.registry import ToolRegistry


# ─── Minimal concrete tool for testing ────────────────────────────────────────────────

class AlwaysSucceedTool(BaseTool):
    name = "always_succeed"
    description = "Returns success unconditionally"

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, data={"ok": True})


class AlwaysFailTool(BaseTool):
    name = "always_fail"
    description = "Always returns failure"
    max_retries = 2
    retry_base_delay = 0.01

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=False, error="intentional failure")


# ─── BaseTool tests ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_successful_tool_returns_result() -> None:
    tool = AlwaysSucceedTool()
    result = await tool.run()
    assert result.success is True
    assert result.data == {"ok": True}


@pytest.mark.asyncio
async def test_failing_tool_exhausts_retries() -> None:
    tool = AlwaysFailTool()
    result = await tool.run()
    assert result.success is False
    assert "2 attempts" in result.error


def test_tool_result_to_dict() -> None:
    r = ToolResult(success=True, data={"x": 1})
    d = r.to_dict()
    assert d == {"success": True, "data": {"x": 1}, "error": None}


# ─── ToolRegistry tests ──────────────────────────────────────────────────────────────

def test_registry_register_and_get() -> None:
    reg = ToolRegistry()
    tool = AlwaysSucceedTool()
    reg.register(tool)
    assert reg.get("always_succeed") is tool


def test_registry_get_missing_raises() -> None:
    reg = ToolRegistry()
    with pytest.raises(KeyError):
        reg.get("nonexistent_tool")


def test_registry_list_tools() -> None:
    reg = ToolRegistry()
    reg.register(AlwaysSucceedTool())
    tools = reg.list_tools()
    assert "always_succeed" in tools
