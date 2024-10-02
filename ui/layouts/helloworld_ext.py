from PIL import ImageDraw

from ui.layouts.helloworld import HelloWorld


class HelloWorldExt(HelloWorld):
    def draw(self, image_draw: ImageDraw):
        super().draw(image_draw)
        image_draw.text((100, 10), "!", fill=(255, 255, 255, 255))
