from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from backend.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an AI browser automation planner. Analyse the user’s natural-language request
and decompose it into an ordered list of atomic browser actions.

Return ONLY a JSON object with a single key \"steps\" whose value is an array.
Each step object MUST have an \"action\" field plus action-specific fields listed below.
Also include a human-readable \"description\" field on every step.

Available actions
─────────────────
open_url              { url }
click_element         { selector, description }
type_text             { selector, text }
extract_text          { selector, variable_name }
wait_for_element      { selector, timeout? }
take_screenshot       { filename? }
navigate_back         {}
scroll_to             { selector }
keyboard_shortcut     { keys, description }
switch_tab            { index }
open_new_tab          { url? }
close_tab             {}
execute_script        { script, description }
store_variable        { name, value }
wait                  { ms }
google_open_drive     { folder_url? }
google_get_sheet_data { spreadsheet_url, sheet_name? }
google_create_colab   { notebook_name }
google_open_colab     { notebook_url }
google_paste_to_colab { content, cell_type? }  # cell_type: code | markdown
confirm_action        { message }              # REQUIRED before any destructive action

Variable interpolation: use \"${variable_name}\" to reference a previously stored variable.

Design rules
─────────────
1. First step should always be take_screenshot to capture initial state.
2. Add a wait step (ms: 2000) after every navigation.
3. Use confirm_action before deleting, overwriting, or sending anything.
4. Store important values with store_variable before using them in later steps.
5. Handle possible sign-in redirects with open_url + wait.
6. Keep steps atomic – one action per object.
"""

_REPLAN_PROMPT = """\
An automation task failed mid-execution. Generate a recovery plan for the REMAINING steps.

Original command:
{command}

Steps already completed successfully:
{completed}

Failed step:
{failed}

Error:
{error}

Provide a revised JSON {{\"steps\": [...]}} that continues towards the original goal,
working around the failure. Do not repeat completed steps.
"""


class PlannerAgent:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def create_plan(
        self,
        command: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return an ordered list of step dicts for the given command."""
        user_content = command
        if context:
            user_content = f"Context: {json.dumps(context)}\n\nCommand: {command}"

        logger.info("Planning: %s", command[:120])
        raw = await self._complete(
            [{"role": "system", "content": _SYSTEM_PROMPT},
             {"role": "user", "content": user_content}]
        )
        return self._extract_steps(raw)

    async def replan(
        self,
        command: str,
        completed_steps: List[Dict],
        failed_step: Dict,
        error: str,
    ) -> List[Dict[str, Any]]:
        """Generate a recovery plan for the steps that remain after a failure."""
        prompt = _REPLAN_PROMPT.format(
            command=command,
            completed=json.dumps(completed_steps, indent=2),
            failed=json.dumps(failed_step, indent=2),
            error=error,
        )
        logger.info("Replanning after error: %s", error[:120])
        raw = await self._complete(
            [{"role": "system", "content": _SYSTEM_PROMPT},
             {"role": "user", "content": prompt}]
        )
        return self._extract_steps(raw)

    async def validate_plan(
        self, plan: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Return a feasibility assessment for the given plan."""
        prompt = (
            "Analyse this automation plan for risks, missing prerequisite steps, "
            "and overall feasibility.\n"
            f"Plan:\n{json.dumps(plan, indent=2)}\n\n"
            'Return JSON: {"feasibility_score": 0-100, "risks": [...], '
            '"suggestions": [...], "is_feasible": true/false}'
        )
        raw = await self._complete(
            [{"role": "system", "content": "You are a browser-automation validator. Return only valid JSON."},
             {"role": "user", "content": prompt}]
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"feasibility_score": 50, "risks": [], "suggestions": [], "is_feasible": True}

    # ─── helpers ──────────────────────────────────────────────────────────────────

    async def _complete(self, messages: list) -> str:
        response = await self._client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=4096,
        )
        return response.choices[0].message.content or "{}"

    @staticmethod
    def _extract_steps(raw: str) -> List[Dict[str, Any]]:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Planner returned invalid JSON: {exc}") from exc

        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            # Accept {"steps": [...]} or any top-level list value
            if "steps" in parsed and isinstance(parsed["steps"], list):
                return parsed["steps"]
            for val in parsed.values():
                if isinstance(val, list):
                    return val
        raise ValueError(f"Cannot extract step list from planner output: {raw[:200]}")
