import re
from functools import partial
from PIL import Image, ImageDraw
from PIL.Image import Image as IMG
from PIL.ImageColor import colormap
from typing import List, Optional, Iterator, Any

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


class Text2Image:
    def __init__(self, lines: List[Line], spacing: int = 4):
        self.lines = lines
        self.spacing = spacing

    @classmethod
    def from_text(
        cls,
        text: str,
        fontsize: int,
        bold: bool = False,
        fill: ColorType = "black",
        spacing: int = 4,
        align: HAlignType = "left",
        stroke_width: int = 0,
        stroke_fill: Optional[ColorType] = None,
        fontname: str = "",
        fallback_fonts: List[str] = [],
    ) -> "Text2Image":
        """
        从文本构建 `Text2Image` 对象

        :参数:
          * ``text``: 文本
          * ``fontsize``: 字体大小
          * ``bold``: 是否加粗
          * ``fill``: 文字颜色
          * ``spacing``: 多行文字间距
          * ``align``: 多行文字对齐方式，默认为靠左
          * ``stroke_width``: 文字描边宽度
          * ``stroke_fill``: 描边颜色
          * ``fontname``: 指定首选字体
          * ``fallback_fonts``: 指定备选字体
        """
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
        return cls(lines, spacing)

    @classmethod
    def from_bbcode_text(
        cls,
        text: str,
        fontsize: int = 30,
        fill: ColorType = "black",
        spacing: int = 6,
        align: HAlignType = "left",
        fontname: str = "",
        fallback_fonts: List[str] = [],
    ) -> "Text2Image":
        """
        从含有 `BBCode` 的文本构建 `Text2Image` 对象

        目前支持的 `BBCode` 标签：
          * ``[align=left|right|center][/align]``: 文字对齐方式
          * ``[color=#66CCFF|red|black][/color]``: 字体颜色
          * ``[font=msyh.ttc][/font]``: 文字字体，需填写完整字体文件名
          * ``[size=30][/size]``: 文字大小
          * ``[b][/b]``: 文字加粗

        :参数:
          * ``text``: 文本
          * ``fontsize``: 字体大小，默认为 30
          * ``fill``: 文字颜色，默认为 `black`
          * ``spacing``: 多行文字间距
          * ``align``: 多行文字对齐方式，默认为靠左
          * ``fontname``: 指定首选字体
          * ``fallback_fonts``: 指定备选字体
        """

        def split_text(
            text: str,
            type: str,
            has_param: bool = True,
            param_pattern: str = "",
            default_param: Any = None,
        ) -> Iterator[Tuple[Any, int, int, int, int]]:
            def parse_tag(
                text: str, offset: int = 0
            ) -> Iterator[Tuple[Any, int, int, int, int]]:
                pattern = rf"=(?P<param>{param_pattern})" if has_param else ""
                for block in re.finditer(
                    rf"(?P<tag>\[{type}{pattern}\](?P<content>.*)\[/{type}\])",
                    text,
                    flags=re.S,
                ):
                    for result in parse_tag(
                        block.group("content"),
                        offset + block.pos + block.start("content"),
                    ):
                        yield result
                    yield (
                        block.group("param") if has_param else True,
                        offset + block.pos + block.start("tag"),
                        offset + block.pos + block.start("content"),
                        offset + block.pos + block.end("content"),
                        offset + block.pos + block.end("tag"),
                    )

            for result in parse_tag(text):
                yield result
            yield (default_param if has_param else False, 0, 0, len(text), len(text))

        split_align = partial(
            split_text,
            type="align",
            has_param=True,
            param_pattern=r"left|right|center",
            default_param=align,
        )

        colors = "|".join(colormap.keys())
        split_color = partial(
            split_text,
            type="color",
            has_param=True,
            param_pattern=rf"#[a-fA-F0-9]{6}|{colors}",
            default_param=fill,
        )

        split_font = partial(
            split_text,
            type="font",
            has_param=True,
            param_pattern=r"\S+\.ttf|\S+\.ttc|\S+\.otf|\S+\.fnt",
            default_param=fontname,
        )

        split_size = partial(
            split_text,
            type="size",
            has_param=True,
            param_pattern=r"\d+",
            default_param=fontsize,
        )

        split_bold = partial(
            split_text,
            type="b",
            has_param=False,
        )

        align_parts = list(split_align(text))
        color_parts = list(split_color(text))
        font_parts = list(split_font(text))
        size_parts = list(split_size(text))
        bold_parts = list(split_bold(text))

        def get_param(
            index: int, parts: list[Tuple[Any, int, int, int, int]]
        ) -> Optional[Any]:
            for param, tag1_start, tag1_end, tag2_start, tag2_end in parts:
                if tag1_start != tag1_end and tag1_start <= index < tag1_end:
                    return None
                if tag2_start != tag2_end and tag2_start <= index < tag2_end:
                    return None
                if tag1_end != tag2_start and tag1_end <= index < tag2_start:
                    return param
            return None

        lines: List[Line] = []
        chars: List[Char] = []
        last_align = align
        for index, char in enumerate(text):
            char_align = get_param(index, align_parts)
            if char_align is None:
                continue
            char_color = get_param(index, color_parts)
            if char_color is None:
                continue
            char_font = get_param(index, font_parts)
            if char_font is None:
                continue
            char_size = get_param(index, size_parts)
            if char_size is None:
                continue
            char_bold = get_param(index, bold_parts)
            if char_bold is None:
                continue
            if char == "\n":
                lines.append(Line(chars, last_align))
                chars = []
                continue
            font = get_proper_font(char, char_bold, char_font, fallback_fonts)
            if not font:
                font = (
                    fallback_fonts_bold[0] if char_bold else fallback_fonts_regular[0]
                )
            if char_align != last_align:
                lines.append(Line(chars, last_align))
                last_align = char_align
                chars = []
            chars.append(Char(char, font, int(char_size), char_color))
        if chars:
            lines.append(Line(chars, last_align))

        return cls(lines, spacing)

    @property
    def width(self) -> int:
        if not self.lines:
            return 0
        return max([line.width for line in self.lines])

    @property
    def height(self) -> int:
        if not self.lines:
            return 0
        return (
            sum([line.ascent for line in self.lines])
            + self.lines[-1].descent
            + self.spacing * (len(self.lines) - 1)
        )

    def wrap(self, width: float) -> "Text2Image":
        new_lines: List[Line] = []
        for line in self.lines:
            new_lines.extend(line.wrap(width))
        self.lines = new_lines
        return self

    def to_image(
        self, bg_color: Optional[ColorType] = None, padding: SizeType = (0, 0)
    ) -> IMG:
        img = Image.new(
            "RGBA",
            (int(self.width + padding[0] * 2), int(self.height + padding[1] * 2)),
            bg_color,  # type: ignore
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
            top += line.ascent + self.spacing

        return img


def text2image(
    text: str,
    bg_color: ColorType = "white",
    padding: SizeType = (10, 10),
    max_width: Optional[int] = None,
    **kwargs,
) -> IMG:
    """
    文字转图片，支持少量 `BBCode` 标签，具体见 `Text2Image` 类的 `from_bbcode_text` 函数

    :参数:
        * ``text``: 文本
        * ``bg_color``: 图片背景颜色
        * ``padding``: 图片边距
        * ``max_width``: 图片最大宽度，不设置则不限宽度
    """
    text2img = Text2Image.from_bbcode_text(text, **kwargs)
    if max_width:
        text2img.wrap(max_width)
    return text2img.to_image(bg_color, padding)
