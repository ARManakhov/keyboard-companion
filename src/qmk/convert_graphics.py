import io
import pathlib
from typing import Union

from PIL import Image

from qmk import painter


def convert_graphics_to_qgf(
    input_path: Union[str, pathlib.Path],
    fmt: str = "rgb565",
    use_deltas: bool = True,
    use_rle: bool = True,
    verbose: bool = False,
) -> bytearray:
    input_path = pathlib.Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input image file does not exist: {input_path}")

    if fmt not in painter.valid_formats:
        raise ValueError(
            f"Output format '{fmt}' is invalid. Allowed: {', '.join(valid_formats.keys())}"
        )

    format_info = painter.valid_formats[fmt]

    input_img = Image.open(input_path)
    out_data = io.BytesIO()
    metadata = []

    input_img.save(
        out_data,
        "QGF",
        use_deltas=use_deltas,
        use_rle=use_rle,
        qmk_format=format_info,
        verbose=verbose,
        metadata=metadata,
    )

    return bytearray(out_data.getvalue())
