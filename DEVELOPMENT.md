# Development Guide

## Project Structure

```
ble5_workspace/
├── custom_components/
│   └── etag_display/           # Home Assistant custom integration
│       ├── __init__.py         # Integration setup/teardown
│       ├── manifest.json       # HA integration metadata
│       ├── config_flow.py      # Configuration UI
│       ├── coordinator.py      # Event-driven update coordinator
│       ├── ble_client.py       # BLE communication wrapper
│       ├── entity.py           # Select and sensor entities
│       ├── select.py           # Select platform
│       ├── sensor.py           # Sensor platform
│       ├── const.py            # Constants (UUIDs, commands)
│       └── strings.json        # UI translations
├── ui/
│   ├── layouts/                # Display layout renderers
│   │   ├── calendar.py         # Calendar events layout
│   │   ├── network_stats.py   # Network statistics layout
│   │   └── todo.py             # Todo list layout (existing)
│   ├── pillow.py               # Rendering engine
│   ├── process_image.py        # BWR conversion
│   └── constants.py            # Display dimensions
├── tests/                      # Test suite
│   ├── conftest.py             # Pytest configuration
│   ├── test_config_flow.py    # Config flow tests
│   ├── test_ble_client.py     # BLE client tests
│   ├── test_coordinator.py    # Coordinator tests
│   ├── test_entities.py       # Entity tests
│   ├── test_layouts.py        # Layout tests
│   └── test_integration.py    # End-to-end tests
├── docs/
│   ├── superpowers/
│   │   ├── specs/              # Design specifications
│   │   └── plans/              # Implementation plans
├── hacs.json                   # HACS configuration
└── README.md                   # User documentation
```

## Prerequisites

### Required

- **Python 3.11+** - Home Assistant requirement
- **Home Assistant 2023.8+** - Target platform
- **Git** - Version control

### Optional (for development)

- **pytest** - Test runner
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **black** - Code formatter
- **ruff** - Fast Python linter
- **mypy** - Type checker

## Development Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/tylerwowen/ble5-workspace.git
cd ble5-workspace
```

### 2. Install Python Dependencies

```bash
# Install with development dependencies (recommended)
pip install -e ".[dev]"

# Or install runtime dependencies only
pip install -e .
```

### 3. Install for Development in Home Assistant

**Option A: Symlink (Recommended for active development)**
```bash
ln -s $(pwd)/custom_components/etag_display ~/.homeassistant/custom_components/etag_display
```

**Option B: Copy (For testing)**
```bash
cp -r custom_components/etag_display ~/.homeassistant/custom_components/
```

### 4. Verify Installation

```bash
# Check Python syntax
python3 -m py_compile custom_components/etag_display/*.py

# Run tests (if pytest installed)
pytest tests/ -v

# Check code quality
black --check custom_components/
ruff check custom_components/
mypy custom_components/etag_display/
```

## Development Workflow

### Running Tests

**Run all tests:**
```bash
cd /path/to/ble5-workspace
pytest tests/ -v
```

**Run specific test file:**
```bash
pytest tests/test_coordinator.py -v
```

**Run specific test:**
```bash
pytest tests/test_coordinator.py::test_coordinator_init -v
```

**Run with coverage:**
```bash
pytest tests/ --cov=custom_components.etag_display --cov-report=html
```

**View coverage report:**
```bash
open htmlcov/index.html
```

### Code Quality Checks

**Format code with black:**
```bash
black custom_components/etag_display/
black ui/layouts/
black tests/
```

**Lint with ruff:**
```bash
ruff check custom_components/etag_display/
```

**Type check with mypy:**
```bash
mypy custom_components/etag_display/
```

### Testing in Home Assistant

1. **Enable debug logging** in `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.etag_display: debug
   ```

2. **Restart Home Assistant** after code changes:
   ```bash
   # Via CLI
   ha core restart
   
   # Or via UI
   Settings → System → Restart
   ```

3. **Watch logs:**
   ```bash
   # Live tail
   tail -f ~/.homeassistant/home-assistant.log | grep etag_display
   
   # Or via UI
   Settings → System → Logs
   ```

## Building for Release

### 1. Update Version

Edit `custom_components/etag_display/manifest.json`:
```json
{
  "version": "0.2.0"
}
```

### 2. Create Changelog

Document changes in `CHANGELOG.md` (if you create one):
```markdown
## [0.2.0] - 2026-05-04
### Added
- New feature X
### Fixed
- Bug Y
```

### 3. Create Git Tag

```bash
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

### 4. Create GitHub Release

Go to GitHub → Releases → Create new release
- Tag: v0.2.0
- Title: "E-Tag Display v0.2.0"
- Description: Copy from CHANGELOG.md
- Attach: Optional ZIP of custom_components/etag_display/

HACS will automatically detect the new release.

## Project Dependencies

See `pyproject.toml` for all Python dependencies and `custom_components/etag_display/manifest.json` for Home Assistant integration requirements.

## Architecture

### Event-Driven Updates

```
Home Assistant State Change
    ↓
Event Listener (coordinator._setup_listeners)
    ↓
Debounce (30 seconds)
    ↓
Fetch Data (coordinator._fetch_data)
    ↓
Render Layout (ui/pillow.py)
    ↓
Convert to BWR (ui/process_image.py)
    ↓
Compute Hash (SHA256)
    ↓
Skip if unchanged ← Compare with last_hash
    ↓
Upload via BLE (ble_client.py)
    ↓
Update State (battery, temp, last_update)
```

### Key Design Patterns

1. **Coordinator Pattern** - Central update management
2. **Event-Driven Architecture** - No polling, battery-efficient
3. **Content Hashing** - Prevents unnecessary BLE transfers
4. **Exponential Backoff** - Reliable BLE retry (5s, 10s, 20s)
5. **Debouncing** - Batches rapid changes (30s window)

## Troubleshooting Development Issues

### Tests Fail with Import Errors

**Issue:** `ModuleNotFoundError: No module named 'custom_components'`

**Solution:** Tests use `conftest.py` to add `homeassistant/` to Python path. Run tests from repository root:
```bash
cd /path/to/ble5-workspace
pytest tests/ -v
```

### Home Assistant Doesn't Detect Integration

**Issue:** Integration not showing in Add Integration UI

**Solutions:**
1. Verify directory structure:
   ```bash
   ls -la ~/.homeassistant/custom_components/etag_display/
   ```
   Should contain: `__init__.py`, `manifest.json`, etc.

2. Check `manifest.json` is valid:
   ```bash
   python3 -m json.tool custom_components/etag_display/manifest.json
   ```

3. Restart Home Assistant (required after adding integration)

4. Check logs for errors:
   ```bash
   grep -i "etag_display\|error.*custom_component" ~/.homeassistant/home-assistant.log
   ```

### BLE Connection Fails in Development

**Issue:** `Device not found` errors

**Solutions:**
1. Ensure device is powered and advertising
2. Check Bluetooth integration is enabled
3. Verify service UUID is correct (0xFFF0)
4. Check Bluetooth hardware:
   ```bash
   # Linux
   hciconfig -a
   
   # macOS
   system_profiler SPBluetoothDataType
   ```

### Rendering Errors

**Issue:** `ModuleNotFoundError: No module named 'ui'`

**Solution:** The coordinator adds `ui/` to Python path at runtime. Ensure `ui/` directory exists at repository root with `layouts/`, `pillow.py`, etc.

## Contributing

### Code Style

- **Follow Home Assistant conventions**: See [HA Developer Docs](https://developers.home-assistant.io/)
- **Use type hints**: All functions should have parameter and return type annotations
- **Write docstrings**: Use triple-quoted strings for all classes and public methods
- **Format with black**: `black custom_components/etag_display/`
- **Pass ruff checks**: `ruff check custom_components/etag_display/`

### Commit Messages

Use conventional commits format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `test:` - Adding/updating tests
- `chore:` - Maintenance tasks
- `refactor:` - Code restructuring

Example:
```
feat: add grayscale rendering mode

Implements 8-level grayscale rendering for enhanced image quality
on supported e-paper displays.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Pull Request Process

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Ensure tests pass: `pytest tests/ -v`
5. Format code: `black .`
6. Commit with clear messages
7. Push and create pull request
8. Respond to code review feedback

## Testing Strategy

### Test Pyramid

1. **Unit Tests** (tests/test_*)
   - Test individual components in isolation
   - Mock external dependencies (BLE, HA services)
   - Fast execution, high coverage

2. **Integration Tests** (tests/test_integration.py)
   - Test component interactions
   - Verify full setup/teardown lifecycle
   - Mock only external hardware (BLE devices)

3. **Manual Testing**
   - Install in real Home Assistant instance
   - Test with actual hardware
   - Verify UI flows, BLE communication

### Test Coverage Goals

- **Coordinator**: 80%+ (complex logic)
- **BLE Client**: 70%+ (hardware interaction)
- **Config Flow**: 80%+ (user-facing)
- **Entities**: 70%+ (simple logic)
- **Overall**: 75%+

## Release Checklist

- [ ] All tests passing: `pytest tests/ -v`
- [ ] Code formatted: `black .`
- [ ] No lint errors: `ruff check .`
- [ ] Version bumped in `manifest.json`
- [ ] CHANGELOG updated
- [ ] Git tag created: `v0.x.0`
- [ ] GitHub release created
- [ ] HACS validates integration
- [ ] Manual test in Home Assistant
- [ ] Documentation updated

## Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [HACS Integration Requirements](https://hacs.xyz/docs/publish/integration)
- [CC2640R2 E-Tag Firmware](https://github.com/tylerwowen/cc2640r2-etag)
- [Project Design Spec](docs/superpowers/specs/2026-05-04-home-assistant-etag-integration-design.md)
- [Implementation Plan](docs/superpowers/plans/2026-05-04-home-assistant-etag-integration.md)
