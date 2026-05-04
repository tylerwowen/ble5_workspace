"""BLE client for E-Tag devices using HA bluetooth integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak import BleakClient
from bleak.exc import BleakError

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

from .const import (
    CHAR_BATTERY,
    CHAR_TEMP,
    CHAR_EPD,
    EPD_CMD_RST,
    EPD_CMD_BUF,
    EPD_CMD_BUF_CONT,
    EPD_CMD_BW,
    EPD_CMD_RED,
    EPD_CMD_DP,
    BLE_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class HAETagClient:
    """E-Tag BLE client using HA bluetooth integration."""

    def __init__(self, hass: HomeAssistant, mac_address: str) -> None:
        """Initialize the BLE client."""
        self.hass = hass
        self.mac = mac_address

    async def _get_client(self) -> BleakClient:
        """Get BleakClient for this device."""
        device = bluetooth.async_ble_device_from_address(
            self.hass,
            self.mac,
            connectable=True,
        )

        # Note: This automatically works with BLE proxies (ESPHome)
        # HA's bluetooth integration handles proxy routing transparently

        if not device:
            raise ConnectionError(f"Device {self.mac} not found")

        return BleakClient(device, timeout=BLE_TIMEOUT)

    async def read_battery(self) -> int:
        """Read battery voltage in mV."""
        async with await self._get_client() as client:
            value = await client.read_gatt_char(CHAR_BATTERY)
            # uint16 little-endian
            return int.from_bytes(value, byteorder="little", signed=False)

    async def read_temperature(self) -> int:
        """Read temperature in Celsius."""
        async with await self._get_client() as client:
            value = await client.read_gatt_char(CHAR_TEMP)
            # int8 signed
            return int.from_bytes(value, byteorder="little", signed=True)

    async def write_image(self, bw_data: list[int], red_data: list[int]) -> None:
        """Write BWR image to device."""
        async with await self._get_client() as client:
            # Reset display
            await self._do_cmd(client, EPD_CMD_RST, None)
            await asyncio.sleep(2)  # Wait for reset

            # Send black/white data
            if bw_data:
                await self._do_cmd(client, EPD_CMD_BUF, bw_data)
                await self._do_cmd(client, EPD_CMD_BW, None)

            # Send red data
            if red_data:
                await self._do_cmd(client, EPD_CMD_BUF, red_data)
                await self._do_cmd(client, EPD_CMD_RED, None)

            # Display with LUT 0
            await self._do_cmd(client, EPD_CMD_DP, 0)

    async def _do_cmd(
        self, client: BleakClient, cmd: int, payload: list[int] | int | None
    ) -> None:
        """Send command to device."""
        if isinstance(payload, list):
            # Buffer data - send in chunks
            chunk_size = 60
            for i in range(0, len(payload), chunk_size):
                chunk = payload[i : i + chunk_size]
                chunk_cmd = cmd if i == 0 else EPD_CMD_BUF_CONT
                await client.write_gatt_char(
                    CHAR_EPD,
                    bytes([chunk_cmd] + chunk),
                    response=False,
                )
            return

        # Simple command (no payload or single byte)
        data = [cmd]
        if isinstance(payload, int):
            data.append(payload)

        _LOGGER.debug(f"Sending command: {cmd}")
        await client.write_gatt_char(CHAR_EPD, bytes(data))
