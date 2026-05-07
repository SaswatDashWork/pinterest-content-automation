from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from agents.planner import PlannerAgent


@pytest.mark.asyncio
async def test_create_plan_returns_steps() -> None:
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "steps": [
            {"action": "take_screenshot", "description": "Capture initial state"},
            {"action": "open_url", "url": "https://example.com", "description": "Navigate to target"},
        ]
    })

    with patch("agents.planner.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = MagicMock()
        instance.chat.completions = MagicMock()
        instance.chat.completions.create = AsyncMock(return_value=mock_response)

        planner = PlannerAgent()
        planner._client = instance
        steps = await planner.create_plan("Open example.com and take a screenshot")

    assert len(steps) == 2
    assert steps[0]["action"] == "take_screenshot"
    assert steps[1]["action"] == "open_url"


@pytest.mark.asyncio
async def test_extract_steps_handles_top_level_array() -> None:
    raw = json.dumps([
        {"action": "open_url", "url": "https://x.com", "description": "open"}
    ])
    steps = PlannerAgent._extract_steps(raw)
    assert steps[0]["action"] == "open_url"


def test_extract_steps_raises_on_garbage() -> None:
    with pytest.raises(ValueError):
        PlannerAgent._extract_steps("not json at all")


@pytest.mark.asyncio
async def test_replan_returns_recovery_steps() -> None:
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "steps": [{"action": "navigate_back", "description": "Go back and retry"}]
    })

    with patch("agents.planner.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = MagicMock()
        instance.chat.completions = MagicMock()
        instance.chat.completions.create = AsyncMock(return_value=mock_response)

        planner = PlannerAgent()
        planner._client = instance
        steps = await planner.replan(
            command="do something",
            completed_steps=[],
            failed_step={"action": "click_element", "selector": "#bad"},
            error="Element not found",
        )

    assert steps[0]["action"] == "navigate_back"
