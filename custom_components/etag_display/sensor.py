"""Sensor platform for E-Tag Display integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import ETagSensorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entity for this tag."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ETagSensorEntity(coordinator)])
    _LOGGER.info("Sensor entity set up for %s", entry.data["name"])
