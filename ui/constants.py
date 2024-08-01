from enum import Enum

DISPLAY_SIZE_2IN9 = (296, 128)
DISPLAY_SIZE_2IN66 = (296, 152)
DISPLAY_SIZE_2IN13 = (250, 122)


class LayoutType(Enum):
    HELLOWORLD = 0
    CALENDAR = 1
    TODOS = 2


class DisplaySize(Enum):
    TWO_INCH_NINE = DISPLAY_SIZE_2IN9
    TWO_INCH_SIXTY_SIX = DISPLAY_SIZE_2IN66
    TWO_INCH_THIRTEEN = DISPLAY_SIZE_2IN13
