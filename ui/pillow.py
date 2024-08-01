from ui.constants import LayoutType, DisplaySize
from ui.layouts.helloworld import HelloWorld


def pillow(
    layout_type: str = LayoutType.HELLOWORLD.name,
    size: str = DisplaySize.TWO_INCH_NINE.name,
    data=None,
):
    if data is None:
        data = {}
    # Convert string arguments to enums
    layout_type = LayoutType[layout_type.upper()]
    size = DisplaySize[size.upper()].value

    if layout_type == LayoutType.HELLOWORLD:

        layout = HelloWorld(size, data)
        layout.render()
    else:
        raise ValueError(f"Unknown layout type: {layout_type}")
