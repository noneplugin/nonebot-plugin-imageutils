from typing import Tuple, Union
from typing_extensions import Literal


ModeType = Literal[
    "1", "CMYK", "F", "HSV", "I", "L", "LAB", "P", "RGB", "RGBA", "RGBX", "YCbCr"
]
ColorType = Union[str, Tuple[int, int, int], Tuple[int, int, int, int]]
DrawPosType = Tuple[float, float]
ImgPosType = Tuple[int, int]
XYType = Tuple[float, float, float, float]
BoxType = Tuple[int, int, int, int]
SizeType = Tuple[int, int]
HAlignType = Literal["left", "right", "center"]
VAlignType = Literal["top", "bottom", "center"]
DirectionType = Literal[
    "center",
    "north",
    "south",
    "west",
    "east",
    "northwest",
    "northeast",
    "southwest",
    "southeast",
]
