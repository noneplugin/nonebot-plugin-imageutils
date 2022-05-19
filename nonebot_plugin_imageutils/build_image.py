from io import BytesIO
from pathlib import Path
from PIL.Image import Image as IMG
from typing import List, Union, Optional
from PIL.ImageDraw import ImageDraw as Draw
from PIL import Image, ImageDraw, ImageFilter

from .types import *
from .text2image import Text2Image


class BuildImage:
    def __init__(self, image: IMG):
        self.image = image

    @property
    def width(self) -> int:
        return self.image.width

    @property
    def height(self) -> int:
        return self.image.height

    @property
    def size(self) -> SizeType:
        return self.image.size

    @property
    def draw(self) -> Draw:
        return ImageDraw.Draw(self.image)

    @classmethod
    def new(
        cls, size: SizeType, mode: ModeType = "RGBA", color: Optional[ColorType] = None
    ) -> "BuildImage":
        return cls(Image.new(mode, size, color))  # type: ignore

    @classmethod
    def open(cls, file: Union[str, bytes, BytesIO, Path]) -> "BuildImage":
        return cls(Image.open(file))

    def resize(
        self,
        size: SizeType,
        keep_ratio: bool = False,
        inside: bool = False,
        direction: DirectionType = "center",
        bg_color: ColorType = "white",
        **kwargs
    ) -> "BuildImage":
        """
        调整图片尺寸

        :参数:
          * ``size``: 期望图片大小
          * ``keep_ratio``: 是否保持长宽比，默认为 `False`
          * ``inside``: `keep_ratio` 为 `True` 时，
                        若 `inside` 为 `True`，则调整图片大小至包含于期望尺寸，不足部分设为指定颜色；
                        若 `inside` 为 `False`，则调整图片大小至包含期望尺寸，超出部分裁剪
          * ``direction``: 调整图片大小时图片的方位；默认为居中
          * ``bg_color``: 不足部分设置的颜色
        """
        width, height = size
        if keep_ratio:
            if inside:
                ratio = max(self.width / width, self.height / height)
            else:
                ratio = min(self.width / width, self.height / height)
            width = int(width * ratio)
            height = int(height * ratio)

        self.image = self.image.resize(
            (width, height), resample=Image.ANTIALIAS, **kwargs
        )

        if keep_ratio:
            self.resize_canvas(size, direction, bg_color, **kwargs)
        return self

    def resize_canvas(
        self,
        size: SizeType,
        direction: DirectionType = "center",
        bg_color: ColorType = "white",
    ) -> "BuildImage":
        """
        调整“画布”大小，超出部分裁剪，不足部分设为指定颜色

        :参数:
          * ``img``: 待调整的图片
          * ``size``: 期望图片大小
          * ``direction``: 调整图片大小时图片的方位；默认为居中
          * ``bg_color``: 不足部分设置的颜色
        """
        w, h = size
        x = int((w - self.width) / 2)
        y = int((h - self.height) / 2)
        if direction in ["north", "northwest", "northeast"]:
            y = 0
        elif direction in ["south", "southwest", "southeast"]:
            y = h - self.height
        if direction in ["west", "northwest", "southwest"]:
            x = 0
        elif direction in ["east", "northeast", "southeast"]:
            x = w - self.width
        result = Image.new(self.image.mode, size, bg_color)
        result.paste(self.image, (x, y))
        self.image = result
        return self

    def resize_width(self, width: int, **kwargs) -> "BuildImage":
        """调整图片宽度，不改变长宽比"""
        return self.resize((width, int(self.height * width / self.width)), **kwargs)

    def resize_height(self, height: int, **kwargs) -> "BuildImage":
        """调整图片高度，不改变长宽比"""
        return self.resize((int(self.width * height / self.height), height), **kwargs)

    def rotate(self, angle: float, **kwargs) -> "BuildImage":
        """旋转图片"""
        self.image = self.image.rotate(angle, resample=Image.BICUBIC, **kwargs)
        return self

    def square(self) -> "BuildImage":
        """将图片裁剪为方形"""
        length = min(self.width, self.height)
        return self.resize_canvas((length, length))

    def circle(self) -> "BuildImage":
        """将图片裁剪为圆形"""
        self.square()
        mask = Image.new("L", self.size, 0)
        self.draw.ellipse((1, 1, self.size[0] - 2, self.size[1] - 2), "white")
        mask = mask.filter(ImageFilter.GaussianBlur(0))
        self.image.putalpha(mask)
        return self

    def circle_corner(self, r: int) -> "BuildImage":
        """将图片裁剪为圆角矩形"""
        self.convert("RGBA")
        w, h = self.size
        alpha = self.image.split()[-1]
        circle = Image.new("L", (r * 2, r * 2), 0)  # 创建黑色方形
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, r * 2, r * 2), fill=255)  # 黑色方形内切白色圆形
        alpha.paste(circle.crop((0, 0, r, r)), (0, 0))  # 左上角
        alpha.paste(circle.crop((r, 0, r * 2, r)), (w - r, 0))  # 右上角
        alpha.paste(circle.crop((r, r, r * 2, r * 2)), (w - r, h - r))  # 右下角
        alpha.paste(circle.crop((0, r, r, r * 2)), (0, h - r))  # 左下角
        self.image.putalpha(alpha)
        return self

    def crop(self, box: BoxType) -> "BuildImage":
        """裁剪图片"""
        self.image = self.image.crop(box)
        return self

    def convert(self, mode: ModeType, **kwargs) -> "BuildImage":
        self.image = self.image.convert(mode, **kwargs)
        return self

    def paste(
        self, img: Union[IMG, "BuildImage"], pos: ImgPosType, alpha: bool = False
    ) -> "BuildImage":
        """
        粘贴图片

        :参数:
          * ``img``: 待粘贴的图片
          * ``pos``: 粘贴位置
          * ``alpha``: 图片背景是否为透明
        """
        if isinstance(img, BuildImage):
            img = img.image
        if alpha:
            img = img.convert("RGBA")
            self.image.paste(img, pos, mask=img)
        else:
            self.image.paste(img, pos)
        return self

    def draw_point(
        self, pos: DrawPosType, fill: Optional[ColorType] = None
    ) -> "BuildImage":
        """在图片上画点"""
        self.draw.point(pos, fill=fill)
        return self

    def draw_line(
        self,
        xy: XYType,
        fill: Optional[ColorType] = None,
        width: float = 1,
    ) -> "BuildImage":
        """在图片上画直线"""
        self.draw.line(xy, fill=fill, width=width)
        return self

    def draw_rectangle(
        self,
        xy: XYType,
        fill: Optional[ColorType] = None,
        outline: Optional[ColorType] = None,
        width: float = 1,
    ) -> "BuildImage":
        """在图片上画矩形"""
        self.draw.rectangle(xy, fill, outline, width)
        return self

    def draw_rounded_rectangle(
        self,
        xy: XYType,
        radius: int = 0,
        fill: Optional[ColorType] = None,
        outline: Optional[ColorType] = None,
        width: float = 1,
    ) -> "BuildImage":
        """在图片上画圆角矩形"""
        self.draw.rounded_rectangle(xy, radius, fill, outline, width)
        return self

    def draw_polygon(
        self,
        xy: List[DrawPosType],
        fill: Optional[ColorType] = None,
        outline: Optional[ColorType] = None,
        width: float = 1,
    ) -> "BuildImage":
        """在图片上画多边形"""
        self.draw.polygon(xy, fill, outline, width)
        return self

    def draw_arc(
        self,
        xy: XYType,
        start: float,
        end: float,
        fill: Optional[ColorType] = None,
        width: float = 1,
    ) -> "BuildImage":
        """在图片上画圆弧"""
        self.draw.arc(xy, start, end, fill, width)
        return self

    def draw_ellipse(
        self,
        xy: XYType,
        fill: Optional[ColorType] = None,
        outline: Optional[ColorType] = None,
        width: float = 1,
    ) -> "BuildImage":
        """在图片上画圆"""
        self.draw.ellipse(xy, fill, outline, width)
        return self

    def draw_text(
        self,
        xy: XYType,
        text: str,
        max_fontsize: int = 30,
        min_fontsize: int = 12,
        bold: bool = False,
        fill: ColorType = "black",
        spacing: int = 4,
        halign: HAlignType = "center",
        valign: VAlignType = "center",
        lines_align: HAlignType = "left",
        stroke_ratio: float = 0,
        stroke_fill: Optional[ColorType] = None,
        fontname: str = "",
        fallback_fonts: List[str] = [],
    ) -> "BuildImage":
        """
        在图片上指定区域画文字

        :参数:
          * ``xy``: 文字区域，顺序依次为 左，上，右，下
          * ``text``: 文字，支持多行
          * ``max_fontsize``: 允许的最大字体大小
          * ``min_fontsize``: 允许的最小字体大小
          * ``bold``: 是否加粗
          * ``fill``: 文字颜色
          * ``spacing``: 多行文字间距
          * ``halign``: 横向对齐方式，默认为居中
          * ``valign``: 纵向对齐方式，默认为居中
          * ``lines_align``: 多行文字对齐方式，默认为靠左
          * ``stroke_ratio``: 文字描边的比例，即 描边宽度 / 字体大小
          * ``stroke_fill``: 描边颜色
          * ``fontname``: 指定首选字体
          * ``fallback_fonts``: 指定备选字体
        """

        left = xy[0]
        top = xy[1]
        width = xy[2] - xy[0]
        height = xy[3] - xy[1]
        fontsize = max_fontsize
        while True:
            text2img = Text2Image.from_text(
                text,
                fontsize,
                bold,
                fill,
                spacing,
                lines_align,
                int(fontsize * stroke_ratio),
                stroke_fill,
                fontname,
                fallback_fonts,
            )
            text_w = text2img.width
            text_h = text2img.height
            if text_w > width:
                text2img.wrap(width)
                text_w = text2img.width
                text_h = text2img.height
            if text_h > height:
                fontsize -= 1
                if fontsize < min_fontsize:
                    raise ValueError("在指定的区域和字体大小范围内画不下这段文字")
            else:
                x = left  # "left"
                if halign == "center":
                    x += (width - text_w) / 2
                elif halign == "right":
                    x += width - text_w

                y = top  # "top"
                if valign == "center":
                    y += (height - text_h) / 2
                elif valign == "bottom":
                    y += height - text_h

                self.paste(text2img.to_image(), (int(x), int(y)), alpha=True)
                return self

    def save(self, format: str, **params) -> BytesIO:
        output = BytesIO()
        self.image.save(output, format, **params)
        return output

    def save_jpg(self) -> BytesIO:
        output = BytesIO()
        image = self.image.convert("RGB")
        image.save(output, format="jpeg")
        return output

    def save_png(self) -> BytesIO:
        output = BytesIO()
        image = self.image.convert("RGBA")
        image.save(output, format="png")
        return output
