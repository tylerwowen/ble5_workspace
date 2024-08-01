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

    def render(self):
        with Image.new("RGB", self.size, "white") as im:
            draw = ImageDraw.Draw(im)
            self._draw_bg(draw)

            fnt = ImageFont.truetype("ui/fonts/SanFranciscoDisplay-Regular.otf", 40)
            draw.text((10, 10), "Hello", font=fnt, fill=(0, 0, 0, 255))
            draw.text((10, 50), self.name, font=fnt, fill=(0, 0, 0, 255))
            # write to stdout
            im.save("helloworld.png", "PNG")
