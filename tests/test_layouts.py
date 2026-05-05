"""Tests for new E-Tag layouts."""
import json
import os
from datetime import datetime
import pytest
from PIL import Image

from ui.layouts.calendar import Calendar
from ui.layouts.network_stats import NetworkStats
from ui.constants import DISPLAY_SIZE_2IN9

# Note: These tests must be run from repo root where ui/ is accessible


def test_calendar_renders():
    """Test calendar layout renders without errors."""
    events = [
        {
            "summary": "Team Meeting",
            "start": "2026-05-04T09:00:00",
            "end": "2026-05-04T10:00:00",
        },
        {
            "summary": "Doctor Appt",
            "start": "2026-05-04T14:00:00",
            "end": "2026-05-04T15:00:00",
        },
    ]

    data = {"events": json.dumps(events)}
    layout = Calendar(DISPLAY_SIZE_2IN9, data)

    try:
        # Render should not raise
        layout.render()

        # Output file should exist
        assert os.path.exists("Calendar.png")

        # Verify image dimensions
        with Image.open("Calendar.png") as img:
            assert img.size == DISPLAY_SIZE_2IN9
    finally:
        # Cleanup
        if os.path.exists("Calendar.png"):
            os.remove("Calendar.png")


def test_network_stats_renders():
    """Test network stats layout renders without errors."""
    data = {
        "device_count": "23",
        "bandwidth": "45.2 Mbps",
        "uptime": "7d 3h",
    }

    layout = NetworkStats(DISPLAY_SIZE_2IN9, data)

    try:
        # Render should not raise
        layout.render()

        # Output file should exist
        assert os.path.exists("NetworkStats.png")

        # Verify image dimensions
        with Image.open("NetworkStats.png") as img:
            assert img.size == DISPLAY_SIZE_2IN9
    finally:
        # Cleanup
        if os.path.exists("NetworkStats.png"):
            os.remove("NetworkStats.png")


def test_network_stats_minimal_data():
    """Test network stats with only device count."""
    data = {"device_count": "15"}

    layout = NetworkStats(DISPLAY_SIZE_2IN9, data)

    try:
        layout.render()
        assert os.path.exists("NetworkStats.png")
    finally:
        if os.path.exists("NetworkStats.png"):
            os.remove("NetworkStats.png")
