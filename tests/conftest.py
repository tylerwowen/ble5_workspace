"""Pytest configuration for E-Tag Display tests."""
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock

# Add homeassistant/ to Python path so imports work
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "homeassistant"))


@pytest.fixture
def hass():
    """Mock Home Assistant instance."""
    hass_mock = MagicMock()
    hass_mock.config_entries = MagicMock()
    hass_mock.bus = MagicMock()
    hass_mock.states = MagicMock()
    hass_mock.services = MagicMock()
    return hass_mock


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock()
    entry.data = {
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "mode": "Todos",
        "config": {
            "entity_id": "todo.my_list",
            "show_completed": False,
            "max_items": 10,
        },
    }
    return entry
