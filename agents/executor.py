from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from backend.config import settings

logger = logging.getLogger(__name__)


class ExecutorAgent:
    """
    Drives a Chromium browser via Playwright, dispatching each plan step
    to its corresponding handler method.
    """

    def __init__(self, execution_id: int) -> None:
        self.execution_id = execution_id
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._variables: Dict[str, Any] = {}
        self._screenshots_dir = (
            Path(settings.screenshot_dir) / str(execution_id)
        )
        self._screenshots_dir.mkdir(parents=True, exist_ok=True)
        self._progress_cb: Optional[Callable] = None

    # ─── lifecycle ─────────────────────────────────────────────────────────────────

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.browser_headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        self._page = await self._context.new_page()
        logger.info("Browser started for execution %s", self.execution_id)

    async def stop(self) -> None:
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as exc:
            logger.warning("Browser cleanup error: %s", exc)

    def set_progress_callback(self, cb: Callable) -> None:
        self._progress_cb = cb

    # ─── public execute methods ────────────────────────────────────────────────

    async def execute_plan(
        self,
        steps: List[Dict[str, Any]],
        on_step_complete: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        await self.start()
        completed: List[Dict] = []
        try:
            for i, step in enumerate(steps):
                outcome = await self._run_step(step, i)
                record = {"index": i, "step": step, "result": outcome}

                if on_step_complete:
                    await on_step_complete(i, step, outcome)

                if outcome["status"] == "failed":
                    return {
                        "status": "failed",
                        "completed_steps": completed,
                        "failed_step": record,
                        "error": outcome.get("error"),
                    }
                completed.append(record)

            return {
                "status": "completed",
                "completed_steps": completed,
                "variables": self._variables,
            }
        finally:
            await self.stop()

    # ─── step runner ────────────────────────────────────────────────────────────────

    async def _run_step(self, step: Dict[str, Any], idx: int) -> Dict[str, Any]:
        action = step.get("action", "")
        start = time.time()
        screenshot: Optional[str] = None

        if self._progress_cb:
            await self._progress_cb(idx, step, "running")

        try:
            result = await self._dispatch(action, step)
            duration = int((time.time() - start) * 1000)
            screenshot = await self._screenshot(f"step_{idx}_ok")
            if self._progress_cb:
                await self._progress_cb(idx, step, "completed", result)
            return {"status": "completed", "result": result, "duration_ms": duration, "screenshot": screenshot}
        except Exception as exc:
            duration = int((time.time() - start) * 1000)
            try:
                screenshot = await self._screenshot(f"step_{idx}_err")
            except Exception:
                pass
            err = str(exc)
            logger.error("Step %s (%s) failed: %s", idx, action, err)
            if self._progress_cb:
                await self._progress_cb(idx, step, "failed", error=err)
            return {"status": "failed", "error": err, "duration_ms": duration, "screenshot": screenshot}

    # ─── action dispatcher ──────────────────────────────────────────────────────────

    _HANDLERS: Dict[str, str] = {
        "open_url": "_open_url",
        "click_element": "_click_element",
        "type_text": "_type_text",
        "extract_text": "_extract_text",
        "wait_for_element": "_wait_for_element",
        "take_screenshot": "_take_screenshot_action",
        "navigate_back": "_navigate_back",
        "scroll_to": "_scroll_to",
        "keyboard_shortcut": "_keyboard_shortcut",
        "switch_tab": "_switch_tab",
        "open_new_tab": "_open_new_tab",
        "close_tab": "_close_tab",
        "execute_script": "_execute_script",
        "store_variable": "_store_variable",
        "wait": "_wait",
        "google_open_drive": "_google_open_drive",
        "google_get_sheet_data": "_google_get_sheet_data",
        "google_create_colab": "_google_create_colab",
        "google_open_colab": "_google_open_colab",
        "google_paste_to_colab": "_google_paste_to_colab",
        "confirm_action": "_confirm_action",
    }

    async def _dispatch(self, action: str, step: Dict) -> Any:
        method_name = self._HANDLERS.get(action)
        if not method_name:
            raise ValueError(f"Unknown action: {action}")
        return await getattr(self, method_name)(step)

    # ─── generic browser actions ───────────────────────────────────────────────────

    @property
    def _p(self) -> Page:
        assert self._page is not None, "Browser not started"
        return self._page

    def _var(self, value: Any) -> Any:
        """Resolve ${name} variable references."""
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            return self._variables.get(value[2:-1], value)
        return value

    async def _screenshot(self, name: str) -> str:
        path = str(self._screenshots_dir / f"{name}_{int(time.time())}.png")
        await self._p.screenshot(path=path, full_page=False)
        return path

    async def _open_url(self, step: Dict) -> Dict:
        url = self._var(step["url"])
        await self._p.goto(url, wait_until="networkidle", timeout=settings.browser_timeout)
        return {"url": self._p.url, "title": await self._p.title()}

    async def _click_element(self, step: Dict) -> Dict:
        sel = step["selector"]
        await self._p.wait_for_selector(sel, timeout=settings.browser_timeout)
        await self._p.click(sel)
        return {"clicked": step.get("description", sel)}

    async def _type_text(self, step: Dict) -> Dict:
        sel, text = step["selector"], self._var(step["text"])
        await self._p.wait_for_selector(sel, timeout=settings.browser_timeout)
        await self._p.fill(sel, str(text))
        return {"typed_chars": len(str(text))}

    async def _extract_text(self, step: Dict) -> Dict:
        sel = step["selector"]
        var = step.get("variable_name", "extracted")
        await self._p.wait_for_selector(sel, timeout=settings.browser_timeout)
        text = await self._p.text_content(sel) or ""
        self._variables[var] = text
        return {"variable": var, "preview": text[:200]}

    async def _wait_for_element(self, step: Dict) -> Dict:
        sel = step["selector"]
        timeout = step.get("timeout", settings.browser_timeout)
        await self._p.wait_for_selector(sel, timeout=timeout)
        return {"found": sel}

    async def _take_screenshot_action(self, step: Dict) -> Dict:
        path = await self._screenshot(step.get("filename") or "manual")
        return {"screenshot": path}

    async def _navigate_back(self, _step: Dict) -> Dict:
        await self._p.go_back()
        return {"url": self._p.url}

    async def _scroll_to(self, step: Dict) -> Dict:
        el = await self._p.query_selector(step["selector"])
        if el:
            await el.scroll_into_view_if_needed()
        return {"scrolled_to": step["selector"]}

    async def _keyboard_shortcut(self, step: Dict) -> Dict:
        await self._p.keyboard.press(step["keys"])
        return {"keys": step["keys"]}

    async def _switch_tab(self, step: Dict) -> Dict:
        pages = self._context.pages  # type: ignore[union-attr]
        idx = step.get("index", 0)
        if idx < len(pages):
            self._page = pages[idx]
            await self._page.bring_to_front()
        return {"tab_index": idx}

    async def _open_new_tab(self, step: Dict) -> Dict:
        url = step.get("url", "about:blank")
        new_page = await self._context.new_page()  # type: ignore[union-attr]
        if url != "about:blank":
            await new_page.goto(url, wait_until="networkidle", timeout=settings.browser_timeout)
        self._page = new_page
        return {"url": url}

    async def _close_tab(self, _step: Dict) -> Dict:
        await self._p.close()
        pages = self._context.pages  # type: ignore[union-attr]
        self._page = pages[-1] if pages else None
        return {"closed": True}

    async def _execute_script(self, step: Dict) -> Dict:
        result = await self._p.evaluate(step["script"])
        return {"result": result}

    async def _store_variable(self, step: Dict) -> Dict:
        name = step["name"]
        value = self._var(step.get("value", ""))
        self._variables[name] = value
        return {"stored": name}

    async def _wait(self, step: Dict) -> Dict:
        ms = step.get("ms", 1000)
        await asyncio.sleep(ms / 1000)
        return {"waited_ms": ms}

    async def _confirm_action(self, step: Dict) -> Dict:
        # In MVP the confirmation is auto-approved; a human-in-the-loop variant
        # would pause and emit an SSE event waiting for a frontend response.
        logger.warning("AUTO-CONFIRMED: %s", step.get("message", ""))
        return {"confirmed": True}

    # ─── Google-specific actions ────────────────────────────────────────────────────

    async def _google_open_drive(self, step: Dict) -> Dict:
        url = step.get("folder_url") or "https://drive.google.com"
        await self._p.goto(url, wait_until="networkidle", timeout=settings.browser_timeout)
        await asyncio.sleep(2)
        return {"url": self._p.url}

    async def _google_get_sheet_data(self, step: Dict) -> Dict:
        url = self._var(step["spreadsheet_url"])
        sheet = step.get("sheet_name")
        await self._p.goto(url, wait_until="networkidle", timeout=settings.browser_timeout)
        await asyncio.sleep(4)
        if sheet:
            try:
                await self._p.click(f'[aria-label="{sheet}"]', timeout=5000)
                await asyncio.sleep(2)
            except Exception:
                logger.debug("Sheet tab '%s' not found, using active sheet", sheet)
        await self._p.keyboard.press("Control+a")
        await asyncio.sleep(0.5)
        await self._p.keyboard.press("Control+c")
        return {"copied": True, "url": url}

    async def _google_create_colab(self, step: Dict) -> Dict:
        name = self._var(step.get("notebook_name", "Untitled"))
        await self._p.goto("https://colab.new", wait_until="networkidle", timeout=settings.browser_timeout)
        await asyncio.sleep(3)
        self._variables["colab_url"] = self._p.url
        return {"name": name, "url": self._p.url}

    async def _google_open_colab(self, step: Dict) -> Dict:
        url = self._var(step["notebook_url"])
        await self._p.goto(url, wait_until="networkidle", timeout=settings.browser_timeout)
        await asyncio.sleep(3)
        return {"url": url}

    async def _google_paste_to_colab(self, step: Dict) -> Dict:
        content = self._var(step.get("content", ""))
        cell_type = step.get("cell_type", "code")
        # Try common Colab cell selectors
        for sel in [".cell", ".codecell-input-output", "[data-type='code']", ".inputarea"]:
            try:
                await self._p.click(sel, timeout=4000)
                break
            except Exception:
                continue
        await asyncio.sleep(0.3)
        if cell_type == "markdown":
            await self._p.keyboard.press("Control+m+m")
            await asyncio.sleep(0.3)
        await self._p.keyboard.press("Control+a")
        await asyncio.sleep(0.2)
        await self._p.keyboard.type(str(content))
        return {"pasted": True, "cell_type": cell_type, "chars": len(str(content))}
