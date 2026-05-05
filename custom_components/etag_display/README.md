# E-Tag Display Integration for Home Assistant

A Home Assistant custom integration for CC2640R2-based electronic paper (e-paper) display tags. This integration automatically renders and displays todo lists, calendar events, or network statistics on battery-powered BLE e-paper tags.

## Features

- **Event-Driven Display Updates**: Automatically updates the display when source entities change (todos, calendar events, network stats)
- **Content Deduplication**: Only sends display updates when content actually changes using content hashing
- **Multiple Display Modes**:
  - **Todo Lists**: Display items from any Home Assistant todo list
  - **Calendar**: Show upcoming events from any calendar
  - **Network Stats**: Display device counts, bandwidth, and uptime
- **Battery Monitoring**: Reports battery voltage and percentage
- **Temperature Monitoring**: Shows device temperature from onboard sensor
- **Automatic Image Processing**: Converts rendered content to BWR (Black/White/Red) format optimized for e-paper displays
- **Robust BLE Communication**: Automatic retry with exponential backoff for reliable wireless updates
- **Zero Configuration**: Discovers BLE e-tags automatically via Bluetooth integration

## Requirements

- Home Assistant 2023.8 or later
- Bluetooth integration enabled and configured
- CC2640R2 e-tag device (hardware + firmware from [cc2640r2-etag](https://github.com/yourusername/cc2640r2-etag))
- Python Pillow library (automatically installed)

## Installation

### Method 1: Manual Installation

1. Copy the `etag_display` folder to your `custom_components` directory:
   ```bash
   cd /config
   mkdir -p custom_components
   cp -r /path/to/etag_display custom_components/
   ```

2. Restart Home Assistant

3. Go to Settings → Devices & Services → Add Integration

4. Search for "E-Tag Display" and follow the configuration flow

### Method 2: HACS (Future)

This integration will be available via HACS in the future.

## Configuration

### Initial Setup

1. **Add Integration**:
   - Navigate to Settings → Devices & Services
   - Click "+ ADD INTEGRATION"
   - Search for "E-Tag Display"

2. **Select Device**:
   - The integration will scan for nearby e-tag devices
   - Select your device from the list (identified by MAC address)

3. **Choose Content Mode**:
   - Select one of three display modes:
     - **Todos**: Display a todo list
     - **Calendar**: Display upcoming calendar events
     - **Network Stats**: Display network statistics

4. **Configure Mode-Specific Settings**:

   **For Todo Lists:**
   - `entity_id`: Select the todo list entity to display
   - `show_completed`: Whether to show completed items (default: false)
   - `max_items`: Maximum number of items to display (default: 10)

   **For Calendar:**
   - `entity_id`: Select the calendar entity to display
   - `hours_ahead`: How many hours ahead to show events (default: 24)
   - `max_events`: Maximum number of events to display (default: 5)

   **For Network Stats:**
   - `device_count_entity`: Sensor showing device count (required)
   - `bandwidth_entity`: Sensor showing bandwidth usage (optional)
   - `uptime_entity`: Sensor showing uptime (optional)

### Changing Configuration

To change the display mode or settings after initial setup:

1. Go to Settings → Devices & Services → E-Tag Display
2. Click on the configured device
3. Click "CONFIGURE"
4. Select new mode and update settings

## Usage

### Entities

Each configured e-tag creates two entities:

1. **Select Entity: `select.<name>_display_mode`**
   - Current display mode (Todos, Calendar, NetworkStats)
   - Change mode via the select dropdown
   - Automatically reconfigures listeners and triggers display update

2. **Sensor Entity: `sensor.<name>_display_status`**
   - State: `pending`, `updated`, or `error`
   - Attributes:
     - `mac_address`: Device MAC address
     - `battery_mv`: Battery voltage in millivolts
     - `battery_percent`: Calculated battery percentage (0-100%)
     - `temperature_c`: Temperature in Celsius
     - `content_hash`: First 8 characters of content hash (for debugging)
     - `last_update`: ISO timestamp of last successful update
     - `error`: Error message (if state is `error`)

### Example Automation

**Notify on Low Battery:**

```yaml
automation:
  - alias: "E-Tag Low Battery Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.etag_display_status
        value_template: "{{ state_attr('sensor.etag_display_status', 'battery_percent') }}"
        below: 20
    action:
      - service: notify.mobile_app
        data:
          title: "E-Tag Battery Low"
          message: >
            E-Tag display battery is at {{ state_attr('sensor.etag_display_status', 'battery_percent') }}%
```

**Switch Display Mode Based on Time:**

```yaml
automation:
  - alias: "E-Tag Show Calendar During Work Hours"
    trigger:
      - platform: time
        at: "09:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.etag_display_mode
        data:
          option: "Calendar"
  
  - alias: "E-Tag Show Todos After Work"
    trigger:
      - platform: time
        at: "17:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.etag_display_mode
        data:
          option: "Todos"
```

**Force Display Update:**

```yaml
service: homeassistant.update_entity
target:
  entity_id: sensor.etag_display_status
```

## Troubleshooting

### Device Not Found During Setup

**Symptom**: E-tag device doesn't appear in device list during configuration

**Solutions**:
- Ensure the e-tag is powered on and within Bluetooth range
- Check that Home Assistant's Bluetooth integration is working (Settings → Devices & Services → Bluetooth)
- Verify the e-tag firmware is running correctly (should be advertising with service UUID 0xFFF0)
- Restart the e-tag device (remove and reinsert battery)

### Display Not Updating

**Symptom**: Display shows old content or never updates

**Solutions**:
1. Check sensor status: Look at `sensor.<name>_display_status` for error messages
2. Verify source entity exists and has data
3. Check BLE connection:
   - Ensure device is within range
   - Check for BLE interference from other devices
4. Check logs for BLE errors:
   ```
   Settings → System → Logs
   Filter by "etag_display"
   ```
5. Try manually triggering an update via `homeassistant.update_entity` service

### "Cannot Connect to Device" Error

**Symptom**: Configuration fails with connection error

**Solutions**:
- Device may be too far away - bring it closer to the Home Assistant Bluetooth adapter
- Another Bluetooth connection may be active - wait a few seconds and retry
- Battery may be too low - replace battery
- Check Home Assistant logs for detailed BLE error messages

### Content Shows "Error" State

**Symptom**: `sensor.<name>_display_status` shows "error" state

**Solutions**:
- Check the `error` attribute for specific error message
- Common issues:
  - **BLE timeout**: Device out of range or battery low
  - **Render error**: Invalid entity configuration or missing data
  - **Image conversion error**: Verify Pillow library is installed correctly
- Review logs for detailed stack traces

### Display Update Is Too Frequent

**Symptom**: Display updates multiple times for same content

**Solutions**:
- This shouldn't happen due to content hashing - check logs to see if content hash is changing
- Verify debounce window is working (default: 30 seconds)
- Check that source entity isn't changing rapidly

### Battery Percentage Incorrect

**Symptom**: Battery percentage doesn't match actual battery level

**Solutions**:
- Battery calculation uses linear interpolation between 2000mV (empty) and 3000mV (full)
- Different battery types may have different voltage curves
- To adjust thresholds, modify `BATTERY_FULL` and `BATTERY_EMPTY` constants in `const.py`
- Consider battery voltage (`battery_mv` attribute) as more accurate than percentage

## Technical Details

### Architecture

- **Coordinator Pattern**: Uses `DataUpdateCoordinator` for event-driven updates instead of polling
- **Event Listeners**: Registers listeners on source entities (todos, calendars, sensors) via Home Assistant event bus
- **Debouncing**: 30-second debounce window prevents duplicate updates for rapid state changes
- **Content Hashing**: SHA256 hash of rendered content ensures only actual changes trigger display updates
- **Async BLE**: Non-blocking Bluetooth communication using `bleak` library via Home Assistant's BLE integration
- **Retry Logic**: Exponential backoff retry (5s, 10s, 20s) for failed BLE connections

### BLE Protocol

The integration communicates with e-tags using a custom GATT service:

- **Service UUID**: `0000FFF0-0000-1000-8000-00805F9B34FB`
- **EPD Characteristic**: `0000FFFE-0000-1000-8000-00805F9B34FB`
  - Used for sending image data and display commands
  - Supports fragmented transfers for large images
- **Battery Characteristic**: `0000FFF3-0000-1000-8000-00805F9B34FB`
  - Read-only, returns uint16 voltage in millivolts
- **Temperature Characteristic**: `0000FFF4-0000-1000-8000-00805F9B34FB`
  - Read-only, returns int8 temperature in Celsius

### Display Format

Images are converted to BWR (Black/White/Red) format:
- **Resolution**: 296x128 pixels (configurable via `DISPLAY_WIDTH` and `DISPLAY_HEIGHT`)
- **Color Mapping**:
  - Black: Dark elements (text, lines)
  - White: Background
  - Red: Accents (headers, highlights)
- **Data Format**: Two separate bitmaps (BW and RED) sent sequentially to device

### Rendering Pipeline

1. **Data Collection**: Fetch data from source entities (todos, calendar, sensors)
2. **Layout Rendering**: Use Pillow to render text, icons, and layout
3. **Image Conversion**: Convert RGB image to BWR bitmap using `image_to_bwr_data()`
4. **Fragmentation**: Split bitmap into MTU-sized chunks (typically 20 bytes)
5. **BLE Transfer**: Send chunks sequentially via EPD characteristic
6. **Display Refresh**: Send display command to trigger e-paper refresh

### Performance Characteristics

- **Typical Update Time**: 5-10 seconds (BLE transfer + e-paper refresh)
- **Battery Life**: 6-12 months on CR2450 battery (depending on update frequency)
- **BLE Range**: 10-30 feet (depends on environment and Home Assistant Bluetooth adapter)
- **Update Frequency**: Unlimited, but content deduplication prevents unnecessary refreshes

## Development

### Project Structure

```
etag_display/
├── __init__.py           # Integration setup and entry point
├── config_flow.py        # Configuration flow UI
├── coordinator.py        # DataUpdateCoordinator implementation
├── entity.py            # Select and Sensor entity classes
├── ble_client.py        # BLE communication wrapper
├── const.py             # Constants and configuration
├── strings.json         # UI strings and translations
├── manifest.json        # Integration metadata
└── README.md            # This file
```

### Testing

The integration can be tested without physical hardware using the included mock BLE client:

```python
# In ble_client.py, uncomment the MockETagClient class
# and use it instead of HAETagClient in coordinator.py
```

For full integration testing with actual hardware, see `../../tests/integration_test.py`.

### Contributing

Contributions are welcome! Please:

1. Test changes with actual e-tag hardware
2. Follow Home Assistant's code style (use `black` and `pylint`)
3. Add tests for new features
4. Update this README for user-facing changes

## License

This integration is part of the BLE5 Workspace project. See the root LICENSE file for details.

## Support

For issues, questions, or feature requests:

- **GitHub Issues**: [https://github.com/yourusername/ble5-workspace/issues](https://github.com/yourusername/ble5-workspace/issues)
- **Hardware/Firmware**: See [cc2640r2-etag repository](https://github.com/yourusername/cc2640r2-etag)

## Credits

- E-Tag hardware and firmware based on CC2640R2 BLE SoC from Texas Instruments
- E-paper display drivers adapted from Waveshare EPD libraries
- Integration architecture follows Home Assistant's best practices and patterns
