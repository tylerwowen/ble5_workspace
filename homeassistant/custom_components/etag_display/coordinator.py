"""Coordinator for E-Tag Display integration."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    MODE_TODOS,
    MODE_CALENDAR,
    MODE_NETWORK_STATS,
    DEBOUNCE_WINDOW,
    BLE_RETRY_DELAYS,
    DISPLAY_WIDTH,
    DISPLAY_HEIGHT,
)
from .ble_client import HAETagClient

_LOGGER = logging.getLogger(__name__)


class ETagDisplayCoordinator(DataUpdateCoordinator):
    """E-Tag Display coordinator for event-driven updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,  # Event-driven only
        )

        self.entry = entry
        self.mac = entry.data["mac_address"]
        self.mode = entry.data["mode"]
        self.config = entry.data["config"]

        # State tracking
        self.last_hash: str | None = None
        self.last_update: datetime | None = None
        self.battery: int | None = None
        self.temp: int | None = None
        self.error: str | None = None

        # Debounce handling
        self._update_task: asyncio.Task | None = None
        self._event_listeners: list[callable] = []

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        self._setup_listeners()

        # Trigger initial update
        await self._async_update_display()

    def _setup_listeners(self) -> None:
        """Setup state change listeners based on mode."""
        if self.mode == MODE_TODOS:
            # Listen for changes to the todo entity
            entity_id = self.config["entity_id"]

            @callback
            def todo_state_changed(event: Event) -> None:
                """Handle todo state change."""
                if event.data.get("entity_id") == entity_id:
                    self._debounced_update()

            remove_listener = self.hass.bus.async_listen(
                EVENT_STATE_CHANGED, todo_state_changed
            )
            self._event_listeners.append(remove_listener)

        elif self.mode == MODE_CALENDAR:
            # Listen for changes to the calendar entity
            entity_id = self.config["entity_id"]

            @callback
            def calendar_state_changed(event: Event) -> None:
                """Handle calendar state change."""
                if event.data.get("entity_id") == entity_id:
                    self._debounced_update()

            remove_listener = self.hass.bus.async_listen(
                EVENT_STATE_CHANGED, calendar_state_changed
            )
            self._event_listeners.append(remove_listener)

        elif self.mode == MODE_NETWORK_STATS:
            # Listen for changes to network stat sensors
            device_count_entity = self.config.get("device_count_entity")
            bandwidth_entity = self.config.get("bandwidth_entity")
            uptime_entity = self.config.get("uptime_entity")

            monitored_entities = [
                entity for entity in [device_count_entity, bandwidth_entity, uptime_entity]
                if entity is not None
            ]

            @callback
            def network_stat_changed(event: Event) -> None:
                """Handle network stat change."""
                if event.data.get("entity_id") in monitored_entities:
                    self._debounced_update()

            if monitored_entities:
                remove_listener = self.hass.bus.async_listen(
                    EVENT_STATE_CHANGED, network_stat_changed
                )
                self._event_listeners.append(remove_listener)

    @callback
    def _debounced_update(self) -> None:
        """Schedule debounced update."""
        # Cancel any pending update
        if self._update_task and not self._update_task.done():
            self._update_task.cancel()

        # Schedule update after debounce window
        async def debounced() -> None:
            await asyncio.sleep(DEBOUNCE_WINDOW)
            await self._async_update_display()

        self._update_task = self.hass.async_create_task(debounced())

    def _cleanup_listeners(self) -> None:
        """Remove all event listeners."""
        for remove_listener in self._event_listeners:
            remove_listener()
        self._event_listeners.clear()

    async def _fetch_data(self) -> dict[str, Any]:
        """Fetch data from Home Assistant based on mode."""
        if self.mode == MODE_TODOS:
            return await self._fetch_todo_data()
        elif self.mode == MODE_CALENDAR:
            return await self._fetch_calendar_data()
        elif self.mode == MODE_NETWORK_STATS:
            return await self._fetch_network_stats()
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    async def _fetch_todo_data(self) -> dict[str, Any]:
        """Fetch todo list data from Home Assistant."""
        entity_id = self.config["entity_id"]
        show_completed = self.config.get("show_completed", False)
        max_items = self.config.get("max_items", 10)

        # Call the todo service to get items
        response = await self.hass.services.async_call(
            "todo",
            "get_items",
            {"entity_id": entity_id},
            blocking=True,
            return_response=True,
        )

        # Extract items from response
        items = response.get(entity_id, {}).get("items", [])

        # Filter by completed status
        if not show_completed:
            items = [item for item in items if item.get("status") != "completed"]

        # Limit number of items
        items = items[:max_items]

        # Convert to simplified format
        todos = [
            {
                "title": item.get("summary", ""),
                "done": item.get("status") == "completed",
                "due": item.get("due"),
            }
            for item in items
        ]

        return {"todos": json.dumps(todos)}

    async def _fetch_calendar_data(self) -> dict[str, Any]:
        """Fetch calendar events from Home Assistant."""
        from homeassistant.components.calendar import async_get_events

        entity_id = self.config["entity_id"]
        hours_ahead = self.config.get("hours_ahead", 24)

        # Calculate time range
        start = datetime.now()
        end = start + timedelta(hours=hours_ahead)

        # Fetch events
        events = await async_get_events(self.hass, entity_id, start, end)

        # Convert to simplified format
        calendar_events = [
            {
                "title": event.summary,
                "start": event.start.isoformat(),
                "end": event.end.isoformat(),
                "all_day": event.start == event.start.date(),
            }
            for event in events
        ]

        return {"events": json.dumps(calendar_events)}

    async def _fetch_network_stats(self) -> dict[str, Any]:
        """Fetch network statistics from Home Assistant."""
        stats = {}

        # Device count (required)
        device_count_entity = self.config.get("device_count_entity")
        if device_count_entity:
            state = self.hass.states.get(device_count_entity)
            if state:
                try:
                    stats["device_count"] = int(float(state.state))
                except (ValueError, TypeError):
                    stats["device_count"] = 0
            else:
                stats["device_count"] = 0
        else:
            stats["device_count"] = 0

        # Bandwidth (optional)
        bandwidth_entity = self.config.get("bandwidth_entity")
        if bandwidth_entity:
            state = self.hass.states.get(bandwidth_entity)
            if state:
                try:
                    stats["bandwidth"] = float(state.state)
                except (ValueError, TypeError):
                    stats["bandwidth"] = 0.0
            else:
                stats["bandwidth"] = 0.0

        # Uptime (optional)
        uptime_entity = self.config.get("uptime_entity")
        if uptime_entity:
            state = self.hass.states.get(uptime_entity)
            if state:
                stats["uptime"] = state.state
            else:
                stats["uptime"] = "Unknown"

        return stats

    async def _async_update_display(self) -> None:
        """Update display with current content."""
        # Placeholder - will be implemented in Task 5.4
        pass
