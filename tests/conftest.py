"""Pytest configuration for E-Tag Display tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import ConfigEntry

# Add custom_components to Python path for imports
repo_root = Path(__file__).parent.parent
custom_components_path = repo_root / "custom_components"
if str(custom_components_path) not in sys.path:
    sys.path.insert(0, str(custom_components_path.parent))

# Import the fixtures from pytest-homeassistant-custom-component
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain="etag_display",
        title="E-Tag Display",
        data={
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "name": "Test E-Tag",
            "mode": "Todos",
            "config": {
                "entity_id": "todo.my_list",
                "show_completed": False,
                "max_items": 10,
            },
        },
        source="user",
    )


@pytest.fixture
def mock_ble_device():
    """Mock BLE device."""
    device = MagicMock()
    device.address = "AA:BB:CC:DD:EE:FF"
    device.name = "E-Tag"
    return device
