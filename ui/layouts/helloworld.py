from PIL import Image, ImageDraw, ImageFont
from ui.layouts.base_layout import BaseLayout


class HelloWorld(BaseLayout):
    def __init__(self, size, data=None):
        if data is None:
            data = {"name": "World"}
        self.size = size
        self.name = data.get("name", "World")

    def _draw_bg(self, draw: ImageDraw):
        draw.rectangle((0, 0, self.size[0], self.size[1] / 2), fill="red")

    def _draw_text(self, draw: ImageDraw):
        fnt = ImageFont.truetype("ui/fonts/SanFranciscoDisplay-Regular.otf", 40)
        draw.font = fnt
        draw.fontmode = "1" # Disable antialiasing
        draw.text((10, 10), "Hello", fill=(255, 255, 255, 255))
        draw.text(
            (self.size[0] / 2, self.size[1] / 2 + 10), self.name, fill=(0, 0, 0, 255)
        )

    def render(self):
        with Image.new("RGB", self.size, "white") as im:
            draw = ImageDraw.Draw(im)
            self._draw_bg(draw)
            self._draw_text(draw)
            im.save("helloworld.png", "PNG")
