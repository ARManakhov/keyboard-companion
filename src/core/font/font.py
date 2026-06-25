import subprocess
import tempfile
import pathlib
from typing import List
from core.font.atlas import generate_font_atlas_pil
from qmk.make_font import convert_font_image

asset_path = pathlib.Path(__file__).resolve().parent.parent.parent / "assets"


def generate_and_load_qff_auto(
    unicode_glyphs: str,
    size: int = 12,
    fmt: str = "mono2",
    *,
    default_font: str = str(asset_path / "NotoSans-Regular.ttf"),
    additional_font: List[str] = [
        str(asset_path / "NotoSansCJK-Regular.ttc"),
        str(asset_path / "NotoEmoji-Regular.ttf"),
    ],
) -> bytearray:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        png_path = tmp_path / "font_atlas.png"

        generate_font_atlas_pil(
            default_font=default_font,
            additional_font=additional_font,
            output_png=png_path,
            unicode_glyphs=unicode_glyphs,
            size=size,
        )

        qff_bytes = convert_font_image(
            input_path=png_path,
            fmt=fmt,
            no_ascii=True,
            unicode_glyphs=unicode_glyphs,
            no_rle=False,
        )

        print(f"[QFF] Generated {len(qff_bytes)} bytes")
        return qff_bytes
