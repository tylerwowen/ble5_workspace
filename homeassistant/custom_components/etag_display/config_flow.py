"""Config flow for E-Tag Display integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    BooleanSelector,
)

from .const import (
    DOMAIN,
    SERVICE_UUID,
    MODE_TODOS,
    MODE_CALENDAR,
    MODE_NETWORK_STATS,
    AVAILABLE_MODES,
)

# Note: entity.py will be implemented in Chunk 6

_LOGGER = logging.getLogger(__name__)


class ETagDisplayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for E-Tag Display."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}
        self._selected_device: BluetoothServiceInfoBleak | None = None
        self._selected_mode: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - device discovery."""
        if user_input is not None:
            address = user_input["device"]
            device = self._discovered_devices[address]

            # Check if already configured
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            self._selected_device = device
            return await self.async_step_mode()

        # Discover E-Tag devices
        current_addresses = self._async_current_ids()

        for discovery_info in async_discovered_service_info(self.hass):
            if (
                SERVICE_UUID.lower() in discovery_info.service_uuids
                and discovery_info.address not in current_addresses
            ):
                self._discovered_devices[discovery_info.address] = discovery_info

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        # Build device selection schema
        devices = {
            address: f"{info.name} ({address})"
            for address, info in self._discovered_devices.items()
        }

        data_schema = vol.Schema(
            {
                vol.Required("device"): SelectSelector(
                    SelectSelectorConfig(
                        options=list(devices.keys()),
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    async def async_step_mode(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle mode selection step."""
        if user_input is not None:
            self._selected_mode = user_input["mode"]

            # Route to mode-specific config
            if self._selected_mode == MODE_TODOS:
                return await self.async_step_todo_config()
            elif self._selected_mode == MODE_CALENDAR:
                return await self.async_step_calendar_config()
            elif self._selected_mode == MODE_NETWORK_STATS:
                return await self.async_step_network_config()

        data_schema = vol.Schema(
            {
                vol.Required("mode"): SelectSelector(
                    SelectSelectorConfig(
                        options=AVAILABLE_MODES,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="mode",
            data_schema=data_schema,
        )

    async def async_step_todo_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure todo list source."""
        if user_input is not None:
            return self._create_entry(user_input)

        data_schema = vol.Schema(
            {
                vol.Required("entity_id"): EntitySelector(
                    EntitySelectorConfig(domain="todo")
                ),
                vol.Optional("show_completed", default=False): BooleanSelector(),
                vol.Optional("max_items", default=10): NumberSelector(
                    NumberSelectorConfig(
                        min=1, max=20, mode=NumberSelectorMode.BOX
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="todo_config",
            data_schema=data_schema,
        )

    async def async_step_calendar_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure calendar source."""
        if user_input is not None:
            return self._create_entry(user_input)

        data_schema = vol.Schema(
            {
                vol.Required("entity_id"): EntitySelector(
                    EntitySelectorConfig(domain="calendar")
                ),
                vol.Optional("hours_ahead", default=24): NumberSelector(
                    NumberSelectorConfig(
                        min=1, max=168, mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Optional("max_events", default=5): NumberSelector(
                    NumberSelectorConfig(
                        min=1, max=10, mode=NumberSelectorMode.BOX
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="calendar_config",
            data_schema=data_schema,
        )

    async def async_step_network_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure network stats sources."""
        if user_input is not None:
            return self._create_entry(user_input)

        data_schema = vol.Schema(
            {
                vol.Required("device_count_entity"): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional("bandwidth_entity"): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional("uptime_entity"): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ),
            }
        )

        return self.async_show_form(
            step_id="network_config",
            data_schema=data_schema,
        )

    def _create_entry(self, config: dict[str, Any]) -> FlowResult:
        """Create the config entry."""
        assert self._selected_device is not None
        assert self._selected_mode is not None

        return self.async_create_entry(
            title=self._selected_device.name or self._selected_device.address,
            data={
                "mac_address": self._selected_device.address,
                "name": self._selected_device.name or f"E-Tag {self._selected_device.address[-5:]}",
                "mode": self._selected_mode,
                "config": config,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return ETagOptionsFlow(config_entry)


class ETagOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for E-Tag Display."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update config entry
            new_data = dict(self.config_entry.data)
            new_data["mode"] = user_input.get("mode", new_data["mode"])

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )

            return self.async_create_entry(title="", data={})

        data_schema = vol.Schema(
            {
                vol.Required(
                    "mode",
                    default=self.config_entry.data.get("mode"),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=AVAILABLE_MODES,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
