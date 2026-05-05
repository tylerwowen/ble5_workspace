"""Tests for E-Tag Display entities."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.etag_display.const import MODE_TODOS
from custom_components.etag_display.coordinator import ETagDisplayCoordinator
from custom_components.etag_display.entity import ETagSelectEntity, ETagSensorEntity


@pytest.fixture
def mock_coordinator(hass, mock_config_entry):
    """Mock coordinator."""
    coordinator = ETagDisplayCoordinator(hass, mock_config_entry)
    coordinator.mac = "AA:BB:CC:DD:EE:FF"
    coordinator.mode = MODE_TODOS
    coordinator.last_update = None
    coordinator.battery = 2950
    coordinator.temp = 23
    coordinator.error = None
    coordinator.last_hash = "abc123"
    return coordinator


async def test_select_entity_options(hass: HomeAssistant, mock_coordinator):
    """Test select entity exposes available modes."""
    entity = ETagSelectEntity(mock_coordinator)

    assert entity.options == ["Todos", "Calendar", "NetworkStats"]
    assert entity.current_option == "Todos"


async def test_sensor_entity_state(hass: HomeAssistant, mock_coordinator):
    """Test sensor entity reports correct state."""
    entity = ETagSensorEntity(mock_coordinator)

    # No last_update = pending
    assert entity.native_value == "pending"

    # Set last_update = updated
    from datetime import datetime

    mock_coordinator.last_update = datetime.now()
    assert entity.native_value == "updated"

    # Set error = error
    mock_coordinator.error = "Connection failed"
    assert entity.native_value == "error"


async def test_sensor_entity_attributes(hass: HomeAssistant, mock_coordinator):
    """Test sensor entity exposes correct attributes."""
    from datetime import datetime

    mock_coordinator.last_update = datetime.now()

    entity = ETagSensorEntity(mock_coordinator)

    attrs = entity.extra_state_attributes

    assert attrs["battery_mv"] == 2950
    assert attrs["battery_percent"] == 95  # (2950 - 2000) / 10
    assert attrs["temperature_c"] == 23
    assert attrs["mac_address"] == "AA:BB:CC:DD:EE:FF"
    assert attrs["content_hash"] == "abc123"[:8]
