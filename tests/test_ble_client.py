"""Tests for the E-Tag BLE client."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant

from custom_components.etag_display.ble_client import HAETagClient
from custom_components.etag_display.const import CHAR_BATTERY, CHAR_TEMP


@pytest.fixture
def mock_ble_device():
    """Mock BLE device."""
    device = MagicMock()
    device.address = "AA:BB:CC:DD:EE:FF"
    return device


@pytest.fixture
def mock_bleak_client():
    """Mock BleakClient."""
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock()
    client.read_gatt_char = AsyncMock()
    client.write_gatt_char = AsyncMock()
    return client


async def test_read_battery(hass: HomeAssistant, mock_ble_device, mock_bleak_client):
    """Test reading battery voltage."""
    # Mock battery voltage: 2950mV (0x0B86 little-endian)
    mock_bleak_client.read_gatt_char.return_value = bytes([0x86, 0x0B])

    with patch(
        "custom_components.etag_display.ble_client.bluetooth.async_ble_device_from_address",
        return_value=mock_ble_device,
    ), patch(
        "custom_components.etag_display.ble_client.BleakClient",
        return_value=mock_bleak_client,
    ):
        client = HAETagClient(hass, "AA:BB:CC:DD:EE:FF")
        battery = await client.read_battery()

    assert battery == 2950
    mock_bleak_client.read_gatt_char.assert_called_once_with(CHAR_BATTERY)


async def test_read_temperature(hass: HomeAssistant, mock_ble_device, mock_bleak_client):
    """Test reading temperature."""
    # Mock temperature: 23°C (0x17 signed)
    mock_bleak_client.read_gatt_char.return_value = bytes([0x17])

    with patch(
        "custom_components.etag_display.ble_client.bluetooth.async_ble_device_from_address",
        return_value=mock_ble_device,
    ), patch(
        "custom_components.etag_display.ble_client.BleakClient",
        return_value=mock_bleak_client,
    ):
        client = HAETagClient(hass, "AA:BB:CC:DD:EE:FF")
        temp = await client.read_temperature()

    assert temp == 23
    mock_bleak_client.read_gatt_char.assert_called_once_with(CHAR_TEMP)
