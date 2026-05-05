"""Entity classes for E-Tag Display integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, AVAILABLE_MODES, BATTERY_FULL, BATTERY_EMPTY
from .coordinator import ETagDisplayCoordinator

_LOGGER = logging.getLogger(__name__)


class ETagSelectEntity(SelectEntity):
    """Select entity for choosing display mode."""

    def __init__(self, coordinator: ETagDisplayCoordinator) -> None:
        """Initialize the select entity."""
        self._coordinator = coordinator
        self._attr_name = "Display Mode"
        self._attr_unique_id = f"{coordinator.mac}_mode"
        self._attr_options = AVAILABLE_MODES

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.mac)},
            name=f"E-Tag Display {self._coordinator.mac}",
            manufacturer="DIY",
            model="CC2640R2",
        )

    @property
    def current_option(self) -> str | None:
        """Return current mode."""
        return self._coordinator.mode

    async def async_select_option(self, option: str) -> None:
        """Change the selected mode."""
        if option not in self._attr_options:
            _LOGGER.error(f"Invalid mode: {option}")
            return

        # Update coordinator mode
        self._coordinator.mode = option

        # Update config entry
        self.hass.config_entries.async_update_entry(
            self._coordinator.entry,
            data={
                **self._coordinator.entry.data,
                "mode": option,
            },
        )

        # Cleanup old listeners
        self._coordinator._cleanup_listeners()

        # Setup new listeners for the new mode
        self._coordinator._setup_listeners()

        # Trigger display update
        await self._coordinator._async_update_display()

        # Notify that state changed
        self.async_write_ha_state()


class ETagSensorEntity(SensorEntity):
    """Sensor entity for display status and diagnostics."""

    def __init__(self, coordinator: ETagDisplayCoordinator) -> None:
        """Initialize the sensor entity."""
        self._coordinator = coordinator
        self._attr_name = "Display Status"
        self._attr_unique_id = f"{coordinator.mac}_status"

        # Register as listener to coordinator updates
        coordinator.async_add_listener(self._handle_coordinator_update)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.mac)},
            name=f"E-Tag Display {self._coordinator.mac}",
            manufacturer="DIY",
            model="CC2640R2",
        )

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if self._coordinator.error:
            return "error"
        elif self._coordinator.last_update:
            return "updated"
        else:
            return "pending"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = {
            "mac_address": self._coordinator.mac,
        }

        # Add battery info if available
        if self._coordinator.battery is not None:
            attrs["battery_mv"] = self._coordinator.battery
            attrs["battery_percent"] = self._calculate_battery_percent(
                self._coordinator.battery
            )

        # Add temperature if available
        if self._coordinator.temp is not None:
            attrs["temperature_c"] = self._coordinator.temp

        # Add content hash (first 8 chars) if available
        if self._coordinator.last_hash:
            attrs["content_hash"] = self._coordinator.last_hash[:8]

        # Add last update time if available
        if self._coordinator.last_update:
            attrs["last_update"] = self._coordinator.last_update.isoformat()

        # Add error message if present
        if self._coordinator.error:
            attrs["error"] = self._coordinator.error

        return attrs

    def _calculate_battery_percent(self, battery_mv: int) -> int:
        """Calculate battery percentage from voltage."""
        # Linear interpolation between BATTERY_EMPTY and BATTERY_FULL
        if battery_mv <= BATTERY_EMPTY:
            return 0
        elif battery_mv >= BATTERY_FULL:
            return 100
        else:
            # (voltage - min) / (max - min) * 100
            return int(((battery_mv - BATTERY_EMPTY) / (BATTERY_FULL - BATTERY_EMPTY)) * 100)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
