from PIL import ImageFont
from PIL.ImageDraw import ImageDraw

from ui.layouts.base_layout import BaseLayout


class NetworkStats(BaseLayout):
    """Network statistics layout for E-Tag display.

    Displays device count prominently with optional bandwidth and uptime metrics.
    """

    def __init__(self, size, data=None):
        super().__init__(size, data)
        self.device_count = data.get("device_count", "0")
        self.bandwidth = data.get("bandwidth")
        self.uptime = data.get("uptime")

    def draw(self, image_draw: ImageDraw):
        super().draw(image_draw)

        # Load font (using San Francisco Display for consistency)
        title_font = ImageFont.truetype(
            "ui/fonts/SanFranciscoDisplay-Regular.otf", 18
        )
        large_font = ImageFont.truetype(
            "ui/fonts/SanFranciscoDisplay-Regular.otf", 60
        )
        label_font = ImageFont.truetype(
            "ui/fonts/SanFranciscoDisplay-Regular.otf", 16
        )
        metric_font = ImageFont.truetype(
            "ui/fonts/SanFranciscoDisplay-Regular.otf", 14
        )

        # Disable antialiasing for crisp display
        image_draw.fontmode = "1"

        # Draw title at top
        title = "Network Status"
        image_draw.text((10, 5), title, fill="black", font=title_font)

        # Draw large centered device count
        center_x = self.size[0] // 2
        center_y = self.size[1] // 2 - 15

        image_draw.text(
            (center_x, center_y),
            self.device_count,
            fill="black",
            anchor="mm",
            font=large_font,
        )

        # Draw "devices online" label below count
        label_y = center_y + 35
        image_draw.text(
            (center_x, label_y),
            "devices online",
            fill="black",
            anchor="mm",
            font=label_font,
        )

        # Draw optional metrics at bottom
        metrics_y = self.size[1] - 25
        metrics = []

        if self.bandwidth:
            metrics.append(f"BW: {self.bandwidth}")

        if self.uptime:
            metrics.append(f"Uptime: {self.uptime}")

        if metrics:
            metrics_text = "  |  ".join(metrics)
            image_draw.text(
                (center_x, metrics_y),
                metrics_text,
                fill="black",
                anchor="mm",
                font=metric_font,
            )
