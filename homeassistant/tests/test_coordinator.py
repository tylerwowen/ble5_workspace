"""Test E-Tag Display Coordinator."""
from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.etag_display.coordinator import ETagDisplayCoordinator
from custom_components.etag_display.const import MODE_TODOS, MODE_CALENDAR, MODE_NETWORK_STATS


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    return Mock(
        data={
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "mode": MODE_TODOS,
            "config": {"entity_id": "todo.test", "max_items": 10},
        }
    )


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = Mock()
    hass.async_create_task = lambda coro: coro
    hass.bus.async_listen = Mock(return_value=Mock())
    hass.loop.run_in_executor = AsyncMock()
    return hass


async def test_update_display_skips_unchanged_content(mock_hass, mock_config_entry):
    """Test update skips when content hash matches."""
    coordinator = ETagDisplayCoordinator(mock_hass, mock_config_entry)

    # Set existing hash
    coordinator.last_hash = "abc123"

    # Mock data fetch and rendering
    with patch.object(
        coordinator, "_fetch_data", return_value={"todos": json.dumps([])}
    ), patch(
        "custom_components.etag_display.coordinator.image_to_bwr_data",
        return_value=([0xFF] * 100, [0x00] * 100),
    ), patch.object(
        coordinator, "_render_layout", return_value="/tmp/test.png"
    ):
        # Mock hash computation to return same hash
        with patch(
            "custom_components.etag_display.coordinator.hashlib.sha256"
        ) as mock_hash:
            mock_hash.return_value.hexdigest.return_value = "abc123"

            await coordinator._async_update_display()

        # Verify no BLE update was attempted (skip)
        # (We'll verify this by checking that last_update didn't change)
        assert coordinator.last_update is None
