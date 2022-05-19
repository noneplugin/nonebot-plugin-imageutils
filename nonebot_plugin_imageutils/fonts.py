import anyio
import httpx
import shutil
import traceback
from pathlib import Path
from PIL import ImageFont
from nonebot import get_driver
from nonebot.log import logger
from fontTools.ttLib import TTFont
from PIL.ImageFont import FreeTypeFont
from typing import List, Union, Optional, Set, Iterator

from .config import Config

imageutils_config = Config.parse_obj(get_driver().config.dict())

FONT_PATH = Path("data/fonts")
FONT_PATH.mkdir(parents=True, exist_ok=True)

SPECIAL_FONTSIZES = {"AppleColorEmoji.ttf": 137, "NotoColorEmoji.ttf": 109}


def local_fonts() -> Iterator[str]:
    for f in FONT_PATH.iterdir():
        if f.is_file() and f.suffix in [".otf", ".ttf", ".ttc", ".fnt"]:
            yield f.name


class Font:
    def __init__(self, fontname: str, fontpath: Path, valid_size: Optional[int] = None):
        self.name = fontname
        self.path = fontpath.resolve()
        self.valid_size = valid_size
        """某些字体不支持缩放，只能以特定的大小加载"""
        self._glyph_table: Set[int] = set()
        for table in TTFont(self.path, fontNumber=0)["cmap"].tables:  # type: ignore
            for key in table.cmap.keys():
                self._glyph_table.add(key)

    @classmethod
    def find(cls, fontname: str) -> Optional["Font"]:
        """查找插件路径和系统路径下该名称的字体"""
        if fontname in local_fonts():
            fontpath = FONT_PATH / fontname
            return cls(fontname, fontpath)
        try:
            try:
                fontsize = SPECIAL_FONTSIZES[fontname]
                valid_size = fontsize
            except KeyError:
                fontsize = 10
                valid_size = None
            font = ImageFont.truetype(fontname, fontsize)
            return cls(fontname, Path(str(font.path)), valid_size)
        except OSError:
            return None

    def load_font(self, fontsize: int) -> FreeTypeFont:
        """以指定大小加载字体"""
        return ImageFont.truetype(str(self.path), fontsize, encoding="utf-8")

    def has_char(self, char: str) -> bool:
        """检查字体是否支持某个字符"""
        return ord(char) in self._glyph_table


fallback_fonts_regular: List[Font] = []
fallback_fonts_bold: List[Font] = []


def check_available_fonts():
    for fontname in imageutils_config.pil_fallback_fonts_regular:
        font = Font.find(fontname)
        if font:
            fallback_fonts_regular.append(font)
    for fontname in imageutils_config.pil_fallback_fonts_bold:
        font = Font.find(fontname)
        if font:
            fallback_fonts_bold.append(font)


check_available_fonts()


def get_proper_font(
    char: str,
    bold: bool = False,
    fontname: Optional[str] = None,
    fallback_fonts: List[str] = [],
):
    """
    获取合适的字体，将依次检查备选字体是否支持想要的字符

    :参数:
        * ``char``: 字符
        * ``bold``: 是否粗体
        * ``fontname``: 可选，指定首选字体
        * ``fallback_fonts``: 可选，指定备选字体
    """
    if fontname:
        font = Font.find(fontname)
        if font and font.has_char(char):
            return font
    if fallback_fonts:
        fonts = [Font.find(name) for name in fallback_fonts]
        fonts = [font for font in fonts if font]
    else:
        fonts = fallback_fonts_bold if bold else fallback_fonts_regular
    for font in fonts:
        if font.has_char(char):
            return font


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
