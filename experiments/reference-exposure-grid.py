"""Own linear-exposure reference, not frames rendered by Resolve or OCIO."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, PngImagePlugin


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "experiments/output/exposure-inputs/opaque-srgb16-patches.png"
MANIFEST = ROOT / "docs/experiments/exposure-input-manifest.json"
OUTPUT = ROOT / "experiments/output/exposure-reference"
manifest = json.loads(MANIFEST.read_text("utf-8"))
input_record = next(f for f in manifest["files"] if f["name"] == INPUT.name)
input_sha = hashlib.sha256(INPUT.read_bytes()).hexdigest()
if input_sha != input_record["sha256"]:
    raise RuntimeError("Input differs from the fixed manifest")
samples = manifest["samples"]
if [s["id"] for s in samples] != list(range(16)) or manifest["dimensions"] != [1920, 1080]:
    raise RuntimeError("Reference requires the fixed 4 by 4 patch grid")
encoded = np.array([s["encoded_rgb_u16"] for s in samples], dtype=np.float64) / 65535
linear = np.where(encoded <= 0.04045, encoded / 12.92,
                  ((encoded + 0.055) / 1.055) ** 2.4)
if not np.allclose(linear, [s["realized_linear_rgb"] for s in samples], rtol=0, atol=1e-15):
    raise RuntimeError("Decoded codes differ from the manifest values")
OUTPUT.mkdir(parents=True, exist_ok=True)
png_info = PngImagePlugin.PngInfo()
png_info.add(b"sRGB", b"\0")
cases = []
for ev, name in ((-1, "ev-minus1.png"), (0, "ev-zero.png"), (1, "ev-plus1.png")):
    work = linear * (2.0 ** ev)
    display = np.clip(work, 0, 1)
    display = np.where(display <= 0.0031308, 12.92 * display,
                       1.055 * display ** (1 / 2.4) - 0.055)
    codes = np.floor(display * 255 + 0.5).astype(np.uint8)
    frame = np.empty((1080, 1920, 3), dtype=np.uint8)
    for index, rgb in enumerate(codes):
        row, col = divmod(index, 4)
        frame[row * 270:(row + 1) * 270, col * 480:(col + 1) * 480] = rgb
    path = OUTPUT / name
    Image.fromarray(frame).save(path, pnginfo=png_info)
    cases.append({"ev": ev, "work_range": [float(work.min()), float(work.max())],
                  "samples": [{"id": s["id"], "sample_xy": s["sample_xy"],
                               "work_linear_rgb": work[i].tolist(),
                               "preview_rgb_u8": codes[i].tolist()}
                              for i, s in enumerate(samples)],
                  "preview": {"name": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                              "bytes": path.stat().st_size}})
wrong_encoded = np.clip(encoded[5] * 2, 0, 1)
wrong_linear = np.where(wrong_encoded <= 0.04045, wrong_encoded / 12.92,
                        ((wrong_encoded + 0.055) / 1.055) ** 2.4)
report = {
    "scope": "own_srgb_linear_exposure_reference_no_resolve_or_ocio_execution",
    "input_sha256": input_sha, "source_owned": True,
    "work_convention": "opaque float64 linear RGB, sRGB primaries, D65; RGB_out = RGB_in * 2^EV",
    "preview_convention": "RGB 8-bit sRGB; clamp to [0,1] only for preview, then encode and round half up",
    "sources": ["https://www.w3.org/TR/css-color-4/#color-conversion-code",
                "https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/2831d2547d133b326c6e9a09726ceeb7fe46f997/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp"],
    "limitations": ["Reference samples only; no native Resolve frames or control mapping.",
                    "No alpha, negative-input, HDR, Log or video-encoding validation.",
                    "Preview pixels are not the float work values; values above 1 remain in the table."],
    "cases": cases,
    "negative_control": {"sample_id": 5, "wrong_operation": "multiply sRGB encoded value by 2 and clamp, then decode",
                         "wrong_work_linear_rgb": wrong_linear.tolist(),
                         "correct_plus1_work_linear_rgb": (linear[5] * 2).tolist()},
}
result = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
(OUTPUT / "result.json").write_text(result, "utf-8")
(ROOT / "docs/experiments/exposure-reference-result.json").write_text(result, "utf-8")
print(json.dumps({"scope": report["scope"], "output": str(OUTPUT),
                  "gray_patch": [c["samples"][5]["work_linear_rgb"][0] for c in cases],
                  "wrong_plus1": float(wrong_linear[0])}, ensure_ascii=False))
