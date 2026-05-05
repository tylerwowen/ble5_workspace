"""Integration tests for E-Tag Display integration."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.etag_display import async_setup_entry, async_unload_entry
from custom_components.etag_display.const import DOMAIN, MODE_TODOS
from custom_components.etag_display.coordinator import ETagDisplayCoordinator


@pytest.fixture
def hass():
    """Mock Home Assistant instance."""
    hass_mock = MagicMock()
    hass_mock.data = {}
    hass_mock.config_entries = MagicMock()
    hass_mock.bus = MagicMock()
    hass_mock.states = MagicMock()
    hass_mock.services = MagicMock()
    hass_mock.async_create_task = AsyncMock()
    hass_mock.async_add_executor_job = AsyncMock()

    # Mock async_forward_entry_setups
    hass_mock.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass_mock.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    return hass_mock


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "name": "E-Tag-AABBCC",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "mode": MODE_TODOS,
        "config": {
            "entity_id": "todo.my_list",
            "show_completed": False,
            "max_items": 10,
        },
    }
    return entry


@pytest.mark.asyncio
async def test_integration_setup_success(hass, mock_config_entry):
    """Test full integration setup succeeds."""
    with patch.object(
        ETagDisplayCoordinator, "async_setup", new_callable=AsyncMock
    ) as mock_setup:
        # Act: Setup the integration
        result = await async_setup_entry(hass, mock_config_entry)

        # Assert: Setup returns True
        assert result is True

        # Assert: Coordinator was set up
        mock_setup.assert_called_once()

        # Assert: Coordinator is stored in hass.data
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]

        # Assert: Stored coordinator is correct type
        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]
        assert isinstance(coordinator, ETagDisplayCoordinator)

        # Assert: Coordinator has correct MAC address
        assert coordinator.mac == "AA:BB:CC:DD:EE:FF"

        # Assert: Coordinator has correct mode
        assert coordinator.mode == MODE_TODOS

        # Assert: Coordinator has correct config
        assert coordinator.config["entity_id"] == "todo.my_list"
        assert coordinator.config["show_completed"] is False
        assert coordinator.config["max_items"] == 10

        # Assert: Platforms were forwarded
        hass.config_entries.async_forward_entry_setups.assert_called_once_with(
            mock_config_entry, ["select", "sensor"]
        )


@pytest.mark.asyncio
async def test_integration_unload_success(hass, mock_config_entry):
    """Test integration unload succeeds."""
    with patch.object(
        ETagDisplayCoordinator, "async_setup", new_callable=AsyncMock
    ), patch.object(
        ETagDisplayCoordinator, "_cleanup_listeners", new_callable=MagicMock
    ) as mock_cleanup:
        # Setup first
        await async_setup_entry(hass, mock_config_entry)

        # Act: Unload the integration
        result = await async_unload_entry(hass, mock_config_entry)

        # Assert: Unload returns True
        assert result is True

        # Assert: Coordinator was cleaned up
        mock_cleanup.assert_called_once()

        # Assert: Coordinator is removed from hass.data
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]

        # Assert: Platforms were unloaded
        hass.config_entries.async_unload_platforms.assert_called_once_with(
            mock_config_entry, ["select", "sensor"]
        )


@pytest.mark.asyncio
async def test_multiple_entries_supported(hass):
    """Test multiple config entries can coexist."""
    entry1 = MagicMock()
    entry1.entry_id = "entry_1"
    entry1.data = {
        "name": "E-Tag-001",
        "mac_address": "AA:BB:CC:DD:EE:01",
        "mode": MODE_TODOS,
        "config": {"entity_id": "todo.list_1", "show_completed": False, "max_items": 10},
    }

    entry2 = MagicMock()
    entry2.entry_id = "entry_2"
    entry2.data = {
        "name": "E-Tag-002",
        "mac_address": "AA:BB:CC:DD:EE:02",
        "mode": MODE_TODOS,
        "config": {"entity_id": "todo.list_2", "show_completed": True, "max_items": 5},
    }

    with patch.object(ETagDisplayCoordinator, "async_setup", new_callable=AsyncMock):
        # Setup first entry
        result1 = await async_setup_entry(hass, entry1)
        assert result1 is True

        # Setup second entry
        result2 = await async_setup_entry(hass, entry2)
        assert result2 is True

        # Assert: Both coordinators exist
        assert "entry_1" in hass.data[DOMAIN]
        assert "entry_2" in hass.data[DOMAIN]

        # Assert: Each coordinator has correct MAC
        coord1 = hass.data[DOMAIN]["entry_1"]
        coord2 = hass.data[DOMAIN]["entry_2"]
        assert coord1.mac == "AA:BB:CC:DD:EE:01"
        assert coord2.mac == "AA:BB:CC:DD:EE:02"

        # Assert: Each coordinator has correct config
        assert coord1.config["entity_id"] == "todo.list_1"
        assert coord2.config["entity_id"] == "todo.list_2"
