from ui.layouts.base_layout import BaseLayout
from PIL import ImageDraw


class HalfRed(BaseLayout):
    def draw(self, draw: ImageDraw):
        draw.rectangle((0, 0, self.size[0], self.size[1] / 2), fill="red")
