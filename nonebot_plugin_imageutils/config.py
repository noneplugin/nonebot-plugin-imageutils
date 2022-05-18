from typing import List
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    pil_fallback_fonts_regular: List[str] = [
        "tahoma.ttf",
        "arial.ttf",
        "segoeui.ttf",
        "OpenSans-Regular.ttf",
        "NotoSans-Regular.ttf",
        "msyh.ttc",
        "PingFang-SC-Regular.ttf",
        "SourceHanSansSC-Regular.otf",
        "NotoSansCJK-Regular.ttc",
        "seguiemj.ttf",
        "seguisym.ttf",
        "AppleColorEmoji.ttf",
        "NotoColorEmoji.ttf",
    ]

    pil_fallback_fonts_bold: List[str] = [
        "tahoma.ttf",
        "arialbd.ttf",
        "segoeuib.ttf",
        "OpenSans-Bold.ttf",
        "NotoSans-Bold.ttf",
        "msyhbd.ttc",
        "PingFang-SC-Bold.ttf",
        "SourceHanSansSC-Bold.otf",
        "NotoSansCJK-Bold.ttc",
        "seguiemj.ttf",
        "seguisym.ttf",
        "AppleColorEmoji.ttf",
        "NotoColorEmoji.ttf",
    ]
