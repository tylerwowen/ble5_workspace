from ui.constants import DisplaySize
from ui.layouts import *


def pillow(
    layout_type: str = "HelloWorld",
    size: str = DisplaySize.TWO_INCH_NINE.name,
    data=None,
):
    if data is None:
        data = {}
    size = DisplaySize[size.upper()].value

    # Instantiate the class based on user input class name
    layout_class = globals().get(layout_type)
    if layout_class:
        layout = layout_class(size, data)
    else:
        raise ValueError(f"Unknown layout type: {layout_type}")
    layout.render()
