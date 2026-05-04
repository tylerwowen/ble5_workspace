"""Tests for the E-Tag Display config flow."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.etag_display.const import DOMAIN


@pytest.fixture
def mock_ble_device():
    """Mock BLE device."""
    device = MagicMock()
    device.name = "E-Tag-AABBCC"
    device.address = "AA:BB:CC:DD:EE:FF"
    device.service_uuids = ["0000fff0-0000-1000-8000-00805f9b34fb"]
    return device


async def test_user_step_shows_discovered_devices(
    hass: HomeAssistant, mock_ble_device
):
    """Test user step shows discovered E-Tag devices."""
    with patch(
        "custom_components.etag_display.config_flow.async_discovered_service_info",
        return_value=[mock_ble_device],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "device" in result["data_schema"].schema


async def test_mode_step_shows_available_modes(
    hass: HomeAssistant, mock_ble_device
):
    """Test mode selection step shows available content modes."""
    with patch(
        "custom_components.etag_display.config_flow.async_discovered_service_info",
        return_value=[mock_ble_device],
    ):
        # Complete user step
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"device": mock_ble_device.address},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "mode"
