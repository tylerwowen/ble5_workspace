import logging
import sys
import time
from contextlib import asynccontextmanager

from bleak import BleakClient, BleakScanner
from bleak.uuids import normalize_uuid_16
from rich.progress import track

from .process_image import download_image_if_needed, image_to_bwr_data

# commands support by firmware
EPD_CMD_CLR = 1
EPD_CMD_MODE = 2
EPD_CMD_BUF = 3
EPD_CMD_BUF_CONT = 4
EPD_CMD_LUT = 5
EPD_CMD_RST = 6
EPD_CMD_BW = 7
EPD_CMD_RED = 8
EPD_CMD_DP = 9
EPD_CMD_FILL = 10
EPD_CMD_BUF_PUT = 11
EPD_CMD_BUF_GET = 12
EPD_CMD_SNV_WRITE = 13
EPD_CMD_SNV_READ = 14
EPD_CMD_SAVE_CFG = 15


class Uploader(object):
    def __init__(
        self,
        name_prefix="C26_",
        mac=None,
        log_level=logging.DEBUG,
        timeout=30,
    ):
        self.name_prefix = name_prefix
        self._logger = self._setup_logger(log_level)
        self.timeout = timeout
        self.mac = mac

    def _filter_device(self, device, advertisement_data):
        if not device.name:
            return False
        result = device.name.startswith(self.name_prefix)
        if result:
            self._logger.debug("found device: %s, %s", device, advertisement_data)
        return result

    def _setup_logger(self, log_level):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(name)s - [%(levelname)s] > %(message)s",
        )
        logger = logging.getLogger(__name__)
        logger.level = log_level
        return logger

    @asynccontextmanager
    async def _ble_client(self):
        device = self.mac
        device_str = device
        if not device:
            self._logger.info("starting scan...")
            device = await BleakScanner.find_device_by_filter(
                filterfunc=self._filter_device,
                timeout=self.timeout,
            )
            if device is None:
                self._logger.error(
                    "could not find device with name: %s", self.name_prefix
                )
                raise FileNotFoundError("device not found")
            device_str = device.name if device.name else device.address
        self._logger.info("connecting to device...")

        async with BleakClient(device, timeout=self.timeout) as client:
            self._logger.info("connected to: %s", device_str)
            yield client
            self._logger.info("disconnecting...")
            await client.disconnect()

        self._logger.info("disconnected")

    ##############################################################################################################
    # Private CLI commands
    ##############################################################################################################
    async def _do_cmd(self, client, cmd, payload=None):
        data = [cmd]

        if cmd in [EPD_CMD_MODE, EPD_CMD_DP]:
            data.append(payload)
        elif cmd in [EPD_CMD_CLR, EPD_CMD_RST, EPD_CMD_BW, EPD_CMD_RED]:
            # no need payload
            pass
        elif cmd == EPD_CMD_BUF:
            chunk_size = 60
            for i in track(range(0, len(payload), chunk_size), "Sending buf..."):
                chunk = payload[i : i + chunk_size]
                cmd = cmd if i == 0 else EPD_CMD_BUF_CONT
                # self._logger.debug(f"sending chunk={i+len(chunk)} of data={len(payload)}")
                await client.write_gatt_char(
                    normalize_uuid_16(0xFFFE), bytes([cmd] + chunk), response=False
                )
            return
        else:
            raise Exception(f"unsupported cmd: {cmd}, payload: {payload}")

        self._logger.debug(f"do cmd: {data}")
        await client.write_gatt_char(normalize_uuid_16(0xFFFE), bytes(data))

    async def _upload_image_bwr_data(self, client, bw_data, red_data):
        await self._do_cmd(client, EPD_CMD_RST)
        time.sleep(2)

        if bw_data:
            await self._do_cmd(client, EPD_CMD_BUF, bw_data)
            await self._do_cmd(client, EPD_CMD_BW)
        if red_data:
            await self._do_cmd(client, EPD_CMD_BUF, red_data)
            await self._do_cmd(client, EPD_CMD_RED)
        # display with lut 0
        await self._do_cmd(client, EPD_CMD_DP, 0)

    ##############################################################################################################
    # Public CLI commands
    ##############################################################################################################
    async def read_etag(self):
        async with self._ble_client() as client:
            host_epoch = int(round(time.time()))

            # read current time
            value = await client.read_gatt_char(normalize_uuid_16(0xFFF1))
            epoch = int.from_bytes(value, byteorder="little", signed=False)

            # read time zone
            value = await client.read_gatt_char(normalize_uuid_16(0xFFF2))
            tz_min = int.from_bytes(value, byteorder="little", signed=True)
            self._logger.info(
                f"# host ts: {host_epoch}, etag ts: {epoch}, diff ({epoch - host_epoch})s, tz: {tz_min // 60}h"
            )

            # battery
            value = await client.read_gatt_char(normalize_uuid_16(0xFFF3))
            battery = int.from_bytes(value, byteorder="little", signed=False)

            # temperature
            value = await client.read_gatt_char(normalize_uuid_16(0xFFF4))
            temp = int.from_bytes(value, byteorder="little", signed=True)
            self._logger.info(f"# battery: {battery}mV, temperature: {temp}°C")

            # RTC collaborate
            value = await client.read_gatt_char(normalize_uuid_16(0xFFF5))
            rtc = int.from_bytes(value, byteorder="little", signed=False)
            self._logger.info(f"# rtc: {rtc}")

    async def set_time(self):
        async with self._ble_client() as client:
            epoch = int(round(time.time()))
            self._logger.info(f"setting time: {epoch}")

            # set current time
            await client.write_gatt_char(
                normalize_uuid_16(0xFFF1), epoch.to_bytes(4, byteorder="little")
            )

    # 0: Date mode
    # 1: Image mode
    async def change_mode(self, mode: int):
        if mode not in [0, 1]:
            raise ValueError(f"invalid mode: {mode}")
        async with self._ble_client() as client:
            await self._do_cmd(client, EPD_CMD_MODE, mode)

    # image coule be one of the following:
    # 1. image file path
    # 2. image url
    async def upload_image(self, image: str, width: int = 296, height: int = 128):
        image_path = download_image_if_needed(image)
        # convert 6608697102119889260_296x152.jpg -dither FloydSteinberg -define dither:diffusion-amount=85% -remap palette.png bmp:output.bmp
        bw, red = image_to_bwr_data(image_path, width=width, height=height)
        
        self._logger.debug("size of bw: %d, red: %d", len(bw), len(red))
        for i in range(0, len(bw), 64):
            chunk = bw[i : i + 64]
            hex_chunk = " ".join(f"{byte:02x}" for byte in chunk)
            self._logger.debug(hex_chunk)
        
        try:
            async with self._ble_client() as client:
                await self._upload_image_bwr_data(client, bw, red)
        except FileNotFoundError as e:
            self._logger.error(e)
            sys.exit(1)
