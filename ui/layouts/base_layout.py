import abc

from PIL import Image, ImageDraw


class BaseLayout(metaclass=abc.ABCMeta):
    data = {}
    size = None

    def __init__(self, size, data=None):
        self.size = size
        self.data = data

    @abc.abstractmethod
    def draw(self, image_draw: ImageDraw):
        pass

    def render(self):
        with Image.new("RGB", self.size, "white") as im:
            image_draw = ImageDraw.Draw(im)
            self.draw(image_draw)
            im.save(f"{str(self.__class__.__name__)}.png", "PNG")
