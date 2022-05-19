from PIL import Image, ImageDraw
from PIL.Image import Image as IMG
from typing import List, Optional, Iterator

from .types import *
from .fonts import Font, get_proper_font, fallback_fonts_regular, fallback_fonts_bold


class Char:
    def __init__(
        self,
        char: str,
        font: Font,
        fontsize: int,
        fill: ColorType,
        stroke_width: int = 0,
        stroke_fill: Optional[ColorType] = None,
    ):
        self.char = char
        self.font = font
        self.fontsize = fontsize
        self.fill = fill
        self.stroke_width = stroke_width
        self.stroke_fill = stroke_fill

        if self.font.valid_size:
            self.pilfont = self.font.load_font(self.font.valid_size)
        else:
            self.pilfont = self.font.load_font(fontsize)

        self.ascent, self.descent = self.pilfont.getmetrics()
        self.width, self.height = self.pilfont.getsize(
            self.char, stroke_width=self.stroke_width
        )

        if self.font.valid_size:
            ratio = fontsize / self.font.valid_size
            self.ascent *= ratio
            self.descent *= ratio
            self.width *= ratio
            self.height *= ratio

    def draw_on(self, img: IMG, pos: ImgPosType):
        if self.font.valid_size:
            ratio = self.font.valid_size / self.fontsize
            new_img = Image.new(
                "RGBA", (int(self.width * ratio), int(self.height * ratio))
            )
            draw = ImageDraw.Draw(new_img)
            draw.text(
                (0, 0),
                self.char,
                font=self.pilfont,
                fill=self.fill,
                stroke_width=self.stroke_width,
                stroke_fill=self.stroke_fill,
                embedded_color=True,
            )
            new_img = new_img.resize(
                (int(self.width), int(self.height)), resample=Image.ANTIALIAS
            )
            img.paste(new_img, pos, mask=new_img)
        else:
            draw = ImageDraw.Draw(img)
            draw.text(
                pos,
                self.char,
                font=self.pilfont,
                fill=self.fill,
                stroke_width=self.stroke_width,
                stroke_fill=self.stroke_fill,
                embedded_color=True,
            )


class Line:
    def __init__(self, chars: List[Char], align: HAlignType = "left"):
        self.chars: List[Char] = chars
        self.align: HAlignType = align

    @property
    def width(self) -> int:
        if not self.chars:
            return 0
        return sum([char.width for char in self.chars])

    @property
    def height(self) -> int:
        if not self.chars:
            return 0
        return max([char.height for char in self.chars])

    @property
    def ascent(self) -> int:
        if not self.chars:
            return 0
        return max([char.ascent for char in self.chars])

    @property
    def descent(self) -> int:
        if not self.chars:
            return 0
        return max([char.descent for char in self.chars])

    def wrap(self, width: float) -> Iterator["Line"]:
        last_idx = 0
        for idx in range(len(self.chars)):
            if Line(self.chars[last_idx : idx + 1]).width > width:
                yield Line(self.chars[last_idx:idx], self.align)
                last_idx = idx
        yield Line(self.chars[last_idx:], self.align)


class Text:
    def __init__(
        self,
        text: str,
        fontsize: int,
        bold: bool = False,
        fill: ColorType = "black",
        spacing: int = 4,
        align: HAlignType = "left",
        stroke_width: int = 0,
        stroke_fill: Optional[ColorType] = None,
        fontname: Optional[str] = None,
        fallback_fonts: List[str] = [],
    ):
        self.text = text
        self.spacing = spacing

        lines: List[Line] = []
        chars: List[Char] = []

        for char in text:
            if char == "\n":
                lines.append(Line(chars, align))
                chars = []
                continue
            font = get_proper_font(char, bold, fontname, fallback_fonts)
            if not font:
                font = fallback_fonts_bold[0] if bold else fallback_fonts_regular[0]
            chars.append(Char(char, font, fontsize, fill, stroke_width, stroke_fill))
        if chars:
            lines.append(Line(chars, align))

        self.lines = lines

    @property
    def width(self) -> int:
        if not self.lines:
            return 0
        return max([line.width for line in self.lines])

    @property
    def height(self) -> int:
        if not self.lines:
            return 0
        return sum([line.height for line in self.lines]) + self.spacing * (
            len(self.lines) - 1
        )

    def wrap(self, width: float):
        new_lines: List[Line] = []
        for line in self.lines:
            new_lines.extend(line.wrap(width))
        self.lines = new_lines

    def to_image(self, padding: SizeType = (0, 0)) -> IMG:
        img = Image.new(
            "RGBA",
            (int(self.width + padding[0] * 2), int(self.height + padding[1] * 2)),
        )

        top = padding[1]
        for line in self.lines:
            left = padding[0]  # "left"
            if line.align == "center":
                left += (self.width - line.width) / 2
            elif line.align == "right":
                left += self.width - line.width

            x = left
            for char in line.chars:
                y = top + line.ascent - char.ascent
                char.draw_on(img, (int(x), int(y)))
                x += char.width
            top += line.height + self.spacing

        return img


def text_to_image():
    """TODO"""
    raise NotImplementedError
