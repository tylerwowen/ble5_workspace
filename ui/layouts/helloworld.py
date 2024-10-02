from PIL import ImageDraw, ImageFont

from ui.layouts.half_red import HalfRed


class HelloWorld(HalfRed):
    def __init__(self, size, data=None):
        super().__init__(size, data)
        self.name = data.get("name", "World")

    def draw(self, image_draw: ImageDraw):
        super().draw(image_draw)
        fnt = ImageFont.truetype("ui/fonts/Bookerly.ttf", 40)
        image_draw.font = fnt
        image_draw.fontmode = "1"  # Disable antialiasing
        image_draw.text((10, 10), "Hello", fill="white")
        image_draw.text((self.size[0] / 2, self.size[1] / 2 + 10), self.name, fill="black")
