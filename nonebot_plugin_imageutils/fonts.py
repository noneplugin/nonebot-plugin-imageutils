import anyio
import httpx
import shutil
import traceback
from pathlib import Path
from PIL import ImageFont
from functools import lru_cache
from fontTools.ttLib import TTFont
from collections import namedtuple
from PIL.ImageFont import FreeTypeFont
from matplotlib.ft2font import FT2Font
from typing import List, Union, Optional, Set, Iterator
from matplotlib.font_manager import FontManager, FontProperties

from nonebot import get_driver
from nonebot.log import logger

from .config import Config
from .types import *

imageutils_config = Config.parse_obj(get_driver().config.dict())

FONT_PATH = imageutils_config.custom_font_path or Path("data/fonts")
FONT_PATH.mkdir(parents=True, exist_ok=True)

font_manager = FontManager()


def local_fonts() -> Iterator[str]:
    for f in FONT_PATH.iterdir():
        if f.is_file() and f.suffix in [".otf", ".ttf", ".ttc", ".afm"]:
            yield f.name


def add_font_to_manager(path: Union[str, Path]):
    try:
        font_manager.addfont(path)
    except OSError as exc:
        logger.warning(f"Failed to open font file {path}: {exc}")
    except Exception as exc:
        logger.warning(f"Failed to extract font properties from {path}: {exc}")


for fontname in local_fonts():
    add_font_to_manager(FONT_PATH / fontname)


class Font:
    def __init__(self, family: str, fontpath: Path, valid_size: Optional[int] = None):
        self.family = family
        """字体族名字"""
        self.path = fontpath.resolve()
        """字体文件路径"""
        self.valid_size = valid_size
        """某些字体不支持缩放，只能以特定的大小加载"""
        self._glyph_table: Set[int] = set()
        for table in TTFont(self.path, fontNumber=0)["cmap"].tables:  # type: ignore
            for key in table.cmap.keys():
                self._glyph_table.add(key)

    @classmethod
    @lru_cache()
    def find(
        cls, family: str, style: FontStyle = "normal", weight: FontWeight = "normal"
    ) -> "Font":
        """查找插件路径和系统路径下的字体"""
        font = cls.find_special_font(family)
        if font:
            return font
        filepath = font_manager.findfont(
            FontProperties(family, style=style, weight=weight)  # type: ignore
        )
        font = FT2Font(filepath)
        return cls(font.family_name, Path(font.fname))

    @classmethod
    def find_special_font(cls, family: str) -> Optional["Font"]:
        """查找特殊字体，主要是不可缩放的emoji字体"""

        SpecialFont = namedtuple("SpecialFont", ["family", "fontname", "valid_size"])
        SPECIAL_FONTS = {
            "Apple Color Emoji": SpecialFont(
                "Apple Color Emoji", "AppleColorEmoji.ttf", 137
            ),
            "Noto Color Emoji": SpecialFont(
                "Noto Color Emoji", "NotoColorEmoji.ttf", 109
            ),
        }

        if family in SPECIAL_FONTS:
            prop = SPECIAL_FONTS[family]
            fontname = prop.fontname
            valid_size = prop.valid_size
            fontpath = None
            if fontname in local_fonts():
                fontpath = FONT_PATH / fontname
            else:
                try:
                    font = ImageFont.truetype(fontname, valid_size)
                    fontpath = Path(str(font.path))
                except OSError:
                    pass
            if fontpath:
                return cls(family, fontpath, valid_size)

    def load_font(self, fontsize: int) -> FreeTypeFont:
        """以指定大小加载字体"""
        return ImageFont.truetype(str(self.path), fontsize, encoding="utf-8")

    def has_char(self, char: str) -> bool:
        """检查字体是否支持某个字符"""
        return ord(char) in self._glyph_table


def get_proper_font(
    char: str,
    style: FontStyle = "normal",
    weight: FontWeight = "normal",
    fontname: Optional[str] = None,
    fallback_fonts: List[str] = [],
) -> Font:
    """
    获取合适的字体，将依次检查备选字体是否支持想要的字符

    :参数:
        * ``char``: 字符
        * ``style``: 字体样式，默认为 "normal"
        * ``weight``: 字体粗细，默认为 "normal"
        * ``fontname``: 可选，指定首选字体
        * ``fallback_fonts``: 可选，指定备选字体
    """
    fallback_fonts = fallback_fonts or imageutils_config.default_fallback_fonts
    if fontname:
        fallback_fonts.insert(0, fontname)

    checked_fonts = []
    for family in fallback_fonts:
        font = Font.find(family, style, weight)
        if font.family in checked_fonts:
            continue
        if font.has_char(char):
            return font
    return Font.find(fallback_fonts[0], style, weight)


async def add_font(fontname: str, source: Union[str, Path]):
    """通过字体文件路径或下载链接添加字体到插件路径"""
    fontpath = FONT_PATH / fontname
    if fontpath.exists():
        return
    try:
        if isinstance(source, Path):
            if source.is_file():
                shutil.copyfile(source, fontpath)
        else:
            await download_font(source, fontpath)
        add_font_to_manager(fontpath)
    except:
        logger.warning(
            f"Add font {fontname} from {source} failed\n{traceback.format_exc()}"
        )


async def download_font(url: str, fontpath: Path):
    """下载字体到插件路径"""
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as resp:
            logger.info(f"Begin to download font from <u>{url}</u>")
            total_size = int(resp.headers["Content-Length"])
            downloaded_size = 0
            async with await anyio.open_file(fontpath, "wb") as file:
                async for chunk in resp.aiter_bytes():
                    downloaded_size += await file.write(chunk)
                    logger.trace(
                        f"Download progress: {downloaded_size/total_size:.2%} "
                        f"({downloaded_size}/{total_size} bytes)"
                    )
            if downloaded_size != total_size:
                logger.warning(
                    f"Downloaded size mismatch: {downloaded_size}/{total_size} bytes"
                )
                fontpath.unlink(missing_ok=True)
