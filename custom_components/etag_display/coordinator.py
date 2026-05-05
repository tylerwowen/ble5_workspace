"""Coordinator for E-Tag Display integration."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os

# Import from ui package for rendering
import sys
import tempfile
from datetime import datetime, timedelta
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .ble_client import HAETagClient
from .const import (
    BLE_RETRY_DELAYS,
    DEBOUNCE_WINDOW,
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    DOMAIN,
    MODE_CALENDAR,
    MODE_NETWORK_STATS,
    MODE_TODOS,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))
from ui.constants import DisplaySize
from ui.pillow import pillow
from ui.process_image import image_to_bwr_data

_LOGGER = logging.getLogger(__name__)


class ETagDisplayCoordinator(DataUpdateCoordinator):  # type: ignore[misc]
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
        self._event_listeners: list[Callable] = []

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

            @callback  # type: ignore[untyped-decorator]
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

            @callback  # type: ignore[untyped-decorator]
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
                entity
                for entity in [device_count_entity, bandwidth_entity, uptime_entity]
                if entity is not None
            ]

            @callback  # type: ignore[untyped-decorator]
            def network_stat_changed(event: Event) -> None:
                """Handle network stat change."""
                if event.data.get("entity_id") in monitored_entities:
                    self._debounced_update()

            if monitored_entities:
                remove_listener = self.hass.bus.async_listen(
                    EVENT_STATE_CHANGED, network_stat_changed
                )
                self._event_listeners.append(remove_listener)

    @callback  # type: ignore[untyped-decorator]
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
        stats: dict[str, Any] = {}

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

    async def _render_layout(self, data: dict[str, Any]) -> str:
        """Render layout to image file using ui/pillow module."""
        # Determine layout type based on mode
        if self.mode == MODE_TODOS:
            layout_type = "TodoList"
        elif self.mode == MODE_CALENDAR:
            layout_type = "Calendar"
        elif self.mode == MODE_NETWORK_STATS:
            layout_type = "NetworkStats"
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        # Run rendering in executor (PIL operations are blocking)
        def _render() -> str:
            # Create temporary file for output
            fd, output_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)

            # Render layout
            pillow(
                layout_type=layout_type,
                size=DisplaySize.TWO_INCH_NINE.name,
                data=data,
            )

            # The pillow() function saves to temp dir with layout name
            # We need to find and move it
            temp_dir = tempfile.gettempdir()
            rendered_file = os.path.join(temp_dir, f"{layout_type}.png")

            # Move to our output path
            if os.path.exists(rendered_file):
                os.rename(rendered_file, output_path)
                return output_path
            else:
                raise FileNotFoundError(f"Rendered file not found: {rendered_file}")

        return await self.hass.async_add_executor_job(_render)  # type: ignore[no-any-return]

    async def _upload_with_retry(self, bw_data: list[int], red_data: list[int]) -> None:
        """Upload image to device with exponential backoff retry."""
        client = HAETagClient(self.hass, self.mac)

        for attempt, delay in enumerate(BLE_RETRY_DELAYS, start=1):
            try:
                _LOGGER.debug(f"Upload attempt {attempt}/{len(BLE_RETRY_DELAYS)}")

                # Upload image
                await client.write_image(bw_data, red_data)

                # Read diagnostics after successful upload
                self.battery = await client.read_battery()
                self.temp = await client.read_temperature()

                _LOGGER.info(
                    f"Display updated successfully (battery: {self.battery}mV, temp: {self.temp}C)"
                )
                return

            except Exception as err:
                _LOGGER.warning(f"Upload attempt {attempt} failed: {err}")

                if attempt < len(BLE_RETRY_DELAYS):
                    _LOGGER.debug(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    # Final attempt failed
                    raise

    async def _async_update_display(self) -> None:
        """Update display with current content."""
        try:
            _LOGGER.debug("Starting display update")

            # Step 1: Fetch data from Home Assistant
            data = await self._fetch_data()
            _LOGGER.debug(f"Fetched data: {data}")

            # Step 2: Render layout to image
            image_path = await self._render_layout(data)
            _LOGGER.debug(f"Rendered image: {image_path}")

            # Step 3: Convert to BWR format
            def _convert() -> tuple[list[int], list[int]]:
                return image_to_bwr_data(image_path, DISPLAY_WIDTH, DISPLAY_HEIGHT)  # type: ignore[no-any-return]

            bw_data, red_data = await self.hass.async_add_executor_job(_convert)
            _LOGGER.debug(
                f"Converted to BWR (bw: {len(bw_data)}B, red: {len(red_data)}B)"
            )

            # Clean up temp file
            try:
                os.unlink(image_path)
            except Exception:
                pass

            # Step 4: Compute hash
            content_hash = hashlib.sha256(bytes(bw_data) + bytes(red_data)).hexdigest()
            _LOGGER.debug(f"Content hash: {content_hash}")

            # Step 5: Skip if unchanged
            if content_hash == self.last_hash:
                _LOGGER.info("Content unchanged, skipping upload")
                return

            # Step 6: Upload to device with retry
            await self._upload_with_retry(bw_data, red_data)

            # Step 7: Update state
            self.last_hash = content_hash
            self.last_update = datetime.now()
            self.error = None

            # Notify listeners
            self.async_update_listeners()

        except Exception as err:
            _LOGGER.error(f"Display update failed: {err}", exc_info=True)
            self.error = str(err)
            self.async_update_listeners()
