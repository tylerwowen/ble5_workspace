"""Tests for the E-Tag Display coordinator."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.etag_display.coordinator import ETagDisplayCoordinator
from custom_components.etag_display.const import MODE_TODOS, DOMAIN


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    entry.data = {
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "name": "Test Tag",
        "mode": MODE_TODOS,
        "config": {
            "entity_id": "todo.shopping_list",
            "show_completed": False,
            "max_items": 10,
        },
    }
    return entry


async def test_coordinator_init(hass: HomeAssistant, mock_config_entry):
    """Test coordinator initializes correctly."""
    coordinator = ETagDisplayCoordinator(hass, mock_config_entry)

    assert coordinator.mac == "AA:BB:CC:DD:EE:FF"
    assert coordinator.mode == MODE_TODOS
    assert coordinator.config["entity_id"] == "todo.shopping_list"
    assert coordinator.last_hash is None
    assert coordinator.last_update is None


async def test_setup_listeners_for_todos(hass: HomeAssistant, mock_config_entry):
    """Test listeners are set up for todo mode."""
    coordinator = ETagDisplayCoordinator(hass, mock_config_entry)

    coordinator._setup_listeners()

    # Verify listener was registered
    assert len(coordinator._event_listeners) > 0

    # Cleanup
    coordinator._cleanup_listeners()
    assert len(coordinator._event_listeners) == 0


async def test_fetch_todo_data(hass: HomeAssistant, mock_config_entry):
    """Test fetching todo data from HA."""
    coordinator = ETagDisplayCoordinator(hass, mock_config_entry)

    # Mock todo service response
    mock_response = {
        "todo.shopping_list": {
            "items": [
                {"summary": "Buy milk", "status": "needs_action", "due": "2026-05-05T00:00:00"},
                {"summary": "Buy eggs", "status": "completed", "due": "2026-05-04T00:00:00"},
            ]
        }
    }

    with patch.object(
        hass.services, "async_call", return_value=mock_response
    ) as mock_call:
        data = await coordinator._fetch_data()

        # Verify service was called correctly
        mock_call.assert_called_once_with(
            "todo",
            "get_items",
            {"entity_id": "todo.shopping_list"},
            blocking=True,
            return_response=True,
        )

        # Verify data format
        assert "todos" in data
        todos = json.loads(data["todos"])
        assert len(todos) == 1  # Only incomplete item (show_completed=False)
        assert todos[0]["title"] == "Buy milk"
        assert todos[0]["done"] is False
