from __future__ import annotations

from playwright.async_api import Page

from tools.base_tool import BaseTool, ToolResult
from tools.registry import registry


class OpenURLTool(BaseTool):
    name = "open_url"
    description = "Navigate the browser to any URL"

    def __init__(self, page: Page) -> None:
        self._page = page

    async def execute(self, url: str, **_) -> ToolResult:
        try:
            await self._page.goto(url, wait_until="networkidle", timeout=30_000)
            return ToolResult(success=True, data={"url": self._page.url, "title": await self._page.title()})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class ClickElementTool(BaseTool):
    name = "click_element"
    description = "Click a DOM element identified by CSS selector"

    def __init__(self, page: Page) -> None:
        self._page = page

    async def execute(self, selector: str, **_) -> ToolResult:
        try:
            await self._page.wait_for_selector(selector, timeout=10_000)
            await self._page.click(selector)
            return ToolResult(success=True, data={"clicked": selector})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class TypeTextTool(BaseTool):
    name = "type_text"
    description = "Fill an input field with text"

    def __init__(self, page: Page) -> None:
        self._page = page

    async def execute(self, selector: str, text: str, **_) -> ToolResult:
        try:
            await self._page.wait_for_selector(selector, timeout=10_000)
            await self._page.fill(selector, text)
            return ToolResult(success=True, data={"chars": len(text)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class ExtractTextTool(BaseTool):
    name = "extract_text"
    description = "Read visible text from a DOM element"

    def __init__(self, page: Page) -> None:
        self._page = page

    async def execute(self, selector: str, **_) -> ToolResult:
        try:
            el = await self._page.wait_for_selector(selector, timeout=10_000)
            text = (await el.text_content()) or ""
            return ToolResult(success=True, data={"text": text})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class TakeScreenshotTool(BaseTool):
    name = "take_screenshot"
    description = "Capture the current viewport as a PNG"

    def __init__(self, page: Page, output_dir: str = "./screenshots") -> None:
        self._page = page
        self._dir = output_dir

    async def execute(self, filename: str = "screenshot.png", **_) -> ToolResult:
        import os, time
        path = os.path.join(self._dir, filename or f"{int(time.time())}.png")
        try:
            await self._page.screenshot(path=path, full_page=False)
            return ToolResult(success=True, data={"path": path})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class ExecuteScriptTool(BaseTool):
    name = "execute_script"
    description = "Evaluate JavaScript in the browser context"

    def __init__(self, page: Page) -> None:
        self._page = page

    async def execute(self, script: str, **_) -> ToolResult:
        try:
            result = await self._page.evaluate(script)
            return ToolResult(success=True, data={"result": result})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))
