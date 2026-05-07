from __future__ import annotations

from typing import Dict

from tools.base_tool import BaseTool


class ToolRegistry:
    """Global singleton that maps tool names to instances."""

    _instance: ToolRegistry | None = None

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    @classmethod
    def instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        return self

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"Tool not registered: {name!r}")
        return self._tools[name]

    def list_tools(self) -> Dict[str, str]:
        return {name: tool.description for name, tool in self._tools.items()}

    def __contains__(self, name: str) -> bool:
        return name in self._tools


registry = ToolRegistry.instance()
