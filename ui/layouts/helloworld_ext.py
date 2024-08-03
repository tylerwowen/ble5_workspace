from PIL import ImageDraw
from ui.layouts.helloworld import HelloWorld


class HelloWorldExt(HelloWorld):
    def draw(self, draw: ImageDraw):
        super().draw(draw)
        draw.text((100, 10), "!", fill=(255, 255, 255, 255))
