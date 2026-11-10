"""Create source-owned, opaque SDR stimuli; no Resolve or native DLL is loaded."""
import hashlib
import json
from pathlib import Path
import struct
import zlib

import numpy as np
from PIL import Image

root = Path(__file__).resolve().parents[1]
output = root / "experiments/output/exposure-inputs"
output.mkdir(parents=True, exist_ok=True)
width, height = 1920, 1080
gray = [0, 0.0031308, 0.01, 0.04, 0.09, 0.18, 0.25, 0.5, 0.75, 1]
patches = [(value, value, value) for value in gray] + [
    (0.25, 0, 0), (0, 0.25, 0), (0, 0, 0.25),
    (0, 0.25, 0.25), (0.25, 0, 0.25), (0.25, 0.25, 0),
]
linear = np.empty((height, width, 3), dtype=np.float64)
samples = []
for index, rgb in enumerate(patches):
    row, column = divmod(index, 4)
    x, y = column * 480, row * 270
    linear[y:y + 270, x:x + 480] = rgb
    samples.append({"id": index, "sample_xy": [x + 240, y + 135],
                    "intended_linear_rgb": rgb})

encoded = np.where(linear <= 0.0031308, 12.92 * linear,
                   1.055 * linear ** (1 / 2.4) - 0.055)
codes = np.floor(encoded * 65535 + 0.5).astype(">u2")

def chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data)))

png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 16, 2, 0, 0, 0))
       + chunk(b"sRGB", b"\0")
       + chunk(b"IDAT", zlib.compress(b"".join(b"\0" + row.tobytes() for row in codes)))
       + chunk(b"IEND", b""))
image_path = output / "opaque-srgb16-patches.png"
image_path.write_bytes(png)
with Image.open(image_path) as decoded:
    decoded.load()
    assert decoded.size == (width, height) and decoded.info["srgb"] == 0
preview_path = output / "preview-srgb8.png"
Image.fromarray(np.floor(encoded * 255 + 0.5).astype(np.uint8)).save(preview_path)
for sample in samples:
    x, y = sample["sample_xy"]
    code = codes[y, x].astype(np.float64)
    value = code / 65535
    realized = np.where(value <= 0.04045, value / 12.92,
                        ((value + 0.055) / 1.055) ** 2.4)
    sample["encoded_rgb_u16"] = code.astype(int).tolist()
    sample["realized_linear_rgb"] = realized.tolist()

report = {
    "scope": "generated_stimulus_only_no_resolve_import_or_render",
    "source_owned": True, "dimensions": [width, height], "alpha": "absent_opaque",
    "encoding": "PNG RGB unsigned 16-bit, full range, sRGB chunk intent 0",
    "linear_convention": "sRGB primaries, D65 white, normalized [0,1]",
    "limitations": ["Quantized input; use realized values, not intended values, for comparisons.",
                    "No negative or superwhite samples; no HDR or alpha validation.",
                    "Resolve decoder and color interpretation remain unverified.",
                    "The 8-bit preview is for viewing, not measurement."],
    "files": [{"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
               "bytes": path.stat().st_size} for path in (image_path, preview_path)],
    "samples": samples,
}
(output / "manifest.json").write_text(json.dumps(report, indent=2), "utf-8")
(root / "docs/experiments/exposure-input-manifest.json").write_text(json.dumps(report, indent=2), "utf-8")
print(json.dumps({"output": str(output), "files": report["files"], "samples": len(samples)}))
