from PIL import ImageDraw

from ui.layouts.base_layout import BaseLayout


class HalfRed(BaseLayout):
    def draw(self, image_draw: ImageDraw):
        image_draw.rectangle((0, 0, self.size[0], self.size[1] / 2), fill="red")
