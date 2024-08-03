from PIL import ImageDraw, ImageFont
from ui.layouts.half_red import HalfRed


class HelloWorld(HalfRed):
    def __init__(self, size, data=None):
        super().__init__(size, data)
        self.name = data.get("name", "World")

    def draw(self, draw: ImageDraw):
        super().draw(draw)
        fnt = ImageFont.truetype("ui/fonts/SanFranciscoDisplay-Regular.otf", 40)
        draw.font = fnt
        draw.fontmode = "1"  # Disable antialiasing
        draw.text((10, 10), "Hello", fill="white")
        draw.text((self.size[0] / 2, self.size[1] / 2 + 10), self.name, fill="black")
