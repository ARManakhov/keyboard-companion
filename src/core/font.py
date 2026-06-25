import subprocess
import tempfile
import pathlib
from typing import List
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont, TTCollection


class FontResolver:
    def __init__(
        self, default_font_path: str, font_paths: List[str], size: int = 12
    ) -> None:
        self.font_list = []
        self.font_paths = font_paths
        self.size = size
        self.default_font_path = default_font_path
        self.default_font = ImageFont.truetype(self.default_font_path, self.size)

        self.register_fonts()

    def register_fonts(self) -> None:
        for p in self.font_paths:
            if p.lower().endswith("ttc"):
                try:
                    with TTCollection(p) as collection:
                        for idx, font in enumerate(collection):
                            cmap = font.getBestCmap()
                            if cmap:
                                supported_chars = set(cmap.keys())
                                pil_font = ImageFont.truetype(p, self.size, index=idx)
                                self.font_list.append((pil_font, supported_chars))
                except Exception as e:
                    print(f"Ошибка при чтении коллекции {p}: {e}")
            else:
                try:
                    with TTFont(p) as font:
                        cmap = font.getBestCmap()
                        supported_chars = set(cmap.keys()) if cmap else set()

                        pil_font = ImageFont.truetype(p, self.size)
                        self.font_list.append((pil_font, supported_chars))
                except Exception as e:
                    print(f"Ошибка при чтении шрифта {p}: {e}")

    def resolve_font(self, ch: str) -> ImageFont.FreeTypeFont:
        code = ord(ch)

        for f, cmap in self.font_list:
            if code in cmap:
                return f

        return self.default_font


def _generate_font_atlas_pil(
    default_font: str,
    additional_font: List[str],
    output_png: pathlib.Path,
    unicode_glyphs: str,
    size: int = 12,
) -> None:
    font_resolver = FontResolver(default_font, additional_font, size=size)
    glyphs = []
    for ch in unicode_glyphs:
        glyphs.append(ch)
    glyphs.sort()

    ascent, descent = font_resolver.default_font.getmetrics()
    line_height = ascent + descent

    glyph_info = []
    total_width = 0
    max_bottom = 0

    for ch in glyphs:
        chosen_font = font_resolver.resolve_font(ch)
        bbox = chosen_font.getbbox(ch)
        if bbox:
            left, top, right, bottom = bbox
            w = right - left
            h = bottom - top
        else:
            print(f"no bbox for '{ch}'")
            left = top = 0
            right = bottom = 0
            w = h = 0

        max_bottom = max(max_bottom, bottom)
        glyph_info.append((ch, w, h, left, top, right, bottom, chosen_font))
        total_width += w

    img_height = max(line_height, max_bottom)
    img_width = total_width

    img = Image.new("RGB", (img_width, img_height - 2), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    delimiter = (255, 0, 255)

    x = 0
    for ch, w, h, left, top, right, bottom, chosen_font in glyph_info:
        img.putpixel((x, 0), delimiter)
        draw.text((x - left, -1), ch, font=chosen_font, fill=(255, 255, 255))

        x += w

    img.save(output_png, "PNG")


asset_path = pathlib.Path(__file__).resolve().parent.parent / "assets"

print(asset_path)


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

        _generate_font_atlas_pil(
            default_font=default_font,
            additional_font=additional_font,
            output_png=png_path,
            unicode_glyphs=unicode_glyphs,
            size=size,
        )

        result = subprocess.run(
            [
                "qmk",
                "painter-convert-font-image",
                "--input",
                str(png_path),
                "-f",
                fmt,
                "--unicode-glyphs",
                unicode_glyphs,
                "-n",
                "-w",
            ],
            check=True,
            capture_output=True,
        )

        if result.stdout:
            print(f"[QFF] Got {len(result.stdout)} bytes from stdout")
            return bytearray(result.stdout)

        qff_path = png_path.with_suffix(".qff")
        if qff_path.exists() and qff_path.stat().st_size > 0:
            with open(qff_path, "rb") as f:
                return bytearray(f.read())

        raise RuntimeError("QFF generation failed: no data in stdout or file")
