"""Tests for the E-Tag Display coordinator."""

from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.etag_display.const import MODE_TODOS
from custom_components.etag_display.coordinator import ETagDisplayCoordinator


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
