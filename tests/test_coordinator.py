"""Tests for the E-Tag Display coordinator."""
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
