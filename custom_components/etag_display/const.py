"""Constants for the E-Tag Display integration."""
from typing import Final

DOMAIN: Final = "etag_display"

# BLE Service and Characteristics (full 128-bit UUIDs)
SERVICE_UUID: Final = "0000FFF0-0000-1000-8000-00805F9B34FB"
CHAR_TIME: Final = "0000FFF1-0000-1000-8000-00805F9B34FB"
CHAR_OFFSET: Final = "0000FFF2-0000-1000-8000-00805F9B34FB"
CHAR_BATTERY: Final = "0000FFF3-0000-1000-8000-00805F9B34FB"
CHAR_TEMP: Final = "0000FFF4-0000-1000-8000-00805F9B34FB"
CHAR_RTC_CAL: Final = "0000FFF5-0000-1000-8000-00805F9B34FB"
CHAR_EPD: Final = "0000FFFE-0000-1000-8000-00805F9B34FB"

# EPD Commands (from existing firmware)
EPD_CMD_CLR: Final = 1
EPD_CMD_MODE: Final = 2
EPD_CMD_BUF: Final = 3
EPD_CMD_BUF_CONT: Final = 4
EPD_CMD_LUT: Final = 5
EPD_CMD_RST: Final = 6
EPD_CMD_BW: Final = 7
EPD_CMD_RED: Final = 8
EPD_CMD_DP: Final = 9
EPD_CMD_FILL: Final = 10
EPD_CMD_BUF_PUT: Final = 11
EPD_CMD_BUF_GET: Final = 12
EPD_CMD_SNV_WRITE: Final = 13
EPD_CMD_SNV_READ: Final = 14
EPD_CMD_SAVE_CFG: Final = 15

# Display configuration
DISPLAY_WIDTH: Final = 296
DISPLAY_HEIGHT: Final = 128

# Content modes
MODE_TODOS: Final = "Todos"
MODE_CALENDAR: Final = "Calendar"
MODE_NETWORK_STATS: Final = "NetworkStats"

AVAILABLE_MODES: Final = [MODE_TODOS, MODE_CALENDAR, MODE_NETWORK_STATS]

# Debounce window (seconds)
DEBOUNCE_WINDOW: Final = 30

# BLE retry configuration
BLE_RETRY_DELAYS: Final = [5, 10, 20]  # Exponential backoff delays in seconds
BLE_TIMEOUT: Final = 30  # Connection timeout in seconds

# Battery thresholds (mV)
BATTERY_FULL: Final = 3000
BATTERY_EMPTY: Final = 2000
