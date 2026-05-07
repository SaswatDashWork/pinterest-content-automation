from __future__ import annotations

import asyncio
import logging

from playwright.async_api import Page

from tools.base_tool import BaseTool, ToolResult
from tools.registry import registry

logger = logging.getLogger(__name__)


class GoogleOpenDriveTool(BaseTool):
    name = "google_open_drive"
    description = "Open Google Drive, optionally navigating to a specific folder URL"

    def __init__(self, page: Page) -> None:
        self._page = page

    async def execute(self, folder_url: str = "", **_) -> ToolResult:
        try:
            url = folder_url or "https://drive.google.com"
            await self._page.goto(url, wait_until="networkidle", timeout=30_000)
            await asyncio.sleep(2)
            return ToolResult(success=True, data={"url": self._page.url})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class GoogleGetSheetDataTool(BaseTool):
    name = "google_get_sheet_data"
    description = "Open a Google Sheets URL, optionally select a named sheet, then copy all content"

    def __init__(self, page: Page) -> None:
        self._page = page

    async def execute(self, spreadsheet_url: str, sheet_name: str = "", **_) -> ToolResult:
        try:
            await self._page.goto(spreadsheet_url, wait_until="networkidle", timeout=30_000)
            await asyncio.sleep(4)
            if sheet_name:
                try:
                    await self._page.click(f'[aria-label="{sheet_name}"]', timeout=5000)
                    await asyncio.sleep(2)
                except Exception:
                    logger.debug("Sheet tab '%s' not found", sheet_name)
            await self._page.keyboard.press("Control+a")
            await asyncio.sleep(0.5)
            await self._page.keyboard.press("Control+c")
            return ToolResult(success=True, data={"copied": True, "url": spreadsheet_url})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class GoogleCreateColabTool(BaseTool):
    name = "google_create_colab"
    description = "Create a new Google Colab notebook via colab.new"

    def __init__(self, page: Page) -> None:
        self._page = page

    async def execute(self, notebook_name: str = "Untitled", **_) -> ToolResult:
        try:
            await self._page.goto("https://colab.new", wait_until="networkidle", timeout=30_000)
            await asyncio.sleep(3)
            return ToolResult(success=True, data={"url": self._page.url, "name": notebook_name})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class GoogleOpenColabTool(BaseTool):
    name = "google_open_colab"
    description = "Open an existing Google Colab notebook by URL"

    def __init__(self, page: Page) -> None:
        self._page = page

    async def execute(self, notebook_url: str, **_) -> ToolResult:
        try:
            await self._page.goto(notebook_url, wait_until="networkidle", timeout=30_000)
            await asyncio.sleep(3)
            return ToolResult(success=True, data={"url": notebook_url})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class GooglePasteToColabTool(BaseTool):
    name = "google_paste_to_colab"
    description = "Type content into the active Colab cell (code or markdown)"

    def __init__(self, page: Page) -> None:
        self._page = page

    async def execute(self, content: str, cell_type: str = "code", **_) -> ToolResult:
        try:
            for sel in [".cell", ".codecell-input-output", "[data-type='code']", ".inputarea"]:
                try:
                    await self._page.click(sel, timeout=3000)
                    break
                except Exception:
                    continue
            await asyncio.sleep(0.3)
            if cell_type == "markdown":
                await self._page.keyboard.press("Control+m+m")
                await asyncio.sleep(0.3)
            await self._page.keyboard.press("Control+a")
            await asyncio.sleep(0.2)
            await self._page.keyboard.type(str(content))
            return ToolResult(success=True, data={"pasted": True, "chars": len(content)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class GoogleSaveColabTool(BaseTool):
    name = "google_save_colab"
    description = "Save the current Colab notebook with Ctrl+S"

    def __init__(self, page: Page) -> None:
        self._page = page

    async def execute(self, **_) -> ToolResult:
        try:
            await self._page.keyboard.press("Control+s")
            await asyncio.sleep(1)
            return ToolResult(success=True, data={"saved": True})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


def register_google_tools(page: Page) -> None:
    """Convenience helper to bulk-register all Google tools for a given page."""
    for cls in [
        GoogleOpenDriveTool,
        GoogleGetSheetDataTool,
        GoogleCreateColabTool,
        GoogleOpenColabTool,
        GooglePasteToColabTool,
        GoogleSaveColabTool,
    ]:
        registry.register(cls(page))
