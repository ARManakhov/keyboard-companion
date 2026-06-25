import io
import logging
import os
from pathlib import Path
from typing import Union

from qmk.painter_qff import QFFFont
from qmk.painter import valid_formats


def normpath(path):
    path = Path(path)

    if path.is_absolute():
        return path

    return Path(os.environ["ORIG_CWD"]) / path


class _DummyLogger:
    def error(self, msg, *args, **kwargs):
        logging.error(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        logging.warning(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        logging.info(msg, *args, **kwargs)


def make_font_image(
    font_path: Union[str, Path],
    output_path: Union[str, Path],
    size: int = 12,
    no_ascii: bool = False,
    unicode_glyphs: str = "",
    no_aa: bool = False,
) -> Path:
    font = QFFFont(_DummyLogger())
    font.generate_image(
        ttf_file=Path(font_path),
        font_size=size,
        include_ascii_glyphs=not no_ascii,
        unicode_glyphs=unicode_glyphs,
        use_aa=not no_aa,
    )
    font.save_to_image(Path(output_path))
    return Path(output_path)


def convert_font_image(
    input_path: Union[str, Path],
    fmt: str = "mono2",
    no_ascii: bool = False,
    unicode_glyphs: str = "",
    no_rle: bool = False,
) -> bytearray:
    if fmt not in valid_formats:
        raise ValueError(f"Unknown format '{fmt}'. Valid: {list(valid_formats.keys())}")

    format_info = valid_formats[fmt]

    font = QFFFont(_DummyLogger())
    font.read_from_image(
        img_file=Path(input_path),
        include_ascii_glyphs=not no_ascii,
        unicode_glyphs=unicode_glyphs,
    )

    out = io.BytesIO()
    font.save_to_qff(format_info, use_rle=not no_rle, fp=out)
    return bytearray(out.getvalue())
