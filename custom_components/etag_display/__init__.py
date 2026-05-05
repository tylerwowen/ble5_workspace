"""The E-Tag Display integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import ETagDisplayCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["select", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up E-Tag Display from a config entry."""
    _LOGGER.info("Setting up E-Tag Display for %s", entry.data["name"])

    # Create coordinator for this tag
    coordinator = ETagDisplayCoordinator(hass, entry)

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Setup coordinator (listeners + initial update)
    await coordinator.async_setup()

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading E-Tag Display for %s", entry.data["name"])

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Cleanup listeners
        coordinator._cleanup_listeners()

    return unload_ok
