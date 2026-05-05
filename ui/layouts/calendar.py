"""Calendar layout for displaying daily events."""

import json
from datetime import datetime
from types import SimpleNamespace

from PIL import ImageFont
from PIL.ImageDraw import ImageDraw

from ui.layouts.base_layout import BaseLayout


def event_object_hook(d):
    """Convert ISO datetime strings to datetime objects."""
    if "start" in d:
        d["start"] = datetime.fromisoformat(d["start"])
    if "end" in d:
        d["end"] = datetime.fromisoformat(d["end"])
    return SimpleNamespace(**d)


class Calendar(BaseLayout):
    """Displays today's calendar events with current event highlighted."""

    def __init__(self, size, data=None):
        super().__init__(size, data)
        events_json = data.get("events", "[]")
        self.events = json.loads(events_json, object_hook=event_object_hook)
        # Limit to 5 events
        self.events = self.events[:5]

    def draw(self, image_draw: ImageDraw):
        super().draw(image_draw)

        # Font setup
        title_font = ImageFont.truetype("ui/fonts/SanFranciscoDisplay-Regular.otf", 24)
        event_font = ImageFont.truetype("ui/fonts/SanFranciscoDisplay-Regular.otf", 20)

        image_draw.fontmode = "1"  # Disable antialiasing

        # Draw title "Today"
        title = "Today"
        image_draw.text((10, 10), title, fill="black", font=title_font)

        # Draw horizontal line below title
        title_bbox = image_draw.textbbox((10, 10), title, font=title_font)
        title_bottom = title_bbox[3]
        line_y = title_bottom + 8
        image_draw.line((10, line_y, self.size[0] - 10, line_y), fill="black", width=2)

        # Draw events
        now = datetime.now()
        event_y = line_y + 15
        event_spacing = 22

        for _i, event in enumerate(self.events):
            # Determine if this is the current event
            is_current = event.start <= now < event.end
            fill = "red" if is_current else "black"

            # Format time without leading zero (e.g., "9:00 AM")
            hour = event.start.hour
            minute = event.start.minute
            am_pm = "AM" if hour < 12 else "PM"
            if hour == 0:
                display_hour = 12
            elif hour > 12:
                display_hour = hour - 12
            else:
                display_hour = hour
            time_str = f"{display_hour}:{minute:02d} {am_pm}"

            # Draw marker for current event
            if is_current:
                marker = "▶ "
                marker_x = 10
                image_draw.text(
                    (marker_x, event_y),
                    marker,
                    fill=fill,
                    font=event_font,
                )
                text_x = marker_x + 20
            else:
                text_x = 10

            # Draw time and summary
            event_text = f"{time_str} - {event.summary}"
            image_draw.text((text_x, event_y), event_text, fill=fill, font=event_font)

            event_y += event_spacing
