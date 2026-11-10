"""Independent Decimal-50 oracle and PNG readback for our own reference only."""
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import struct
import zlib

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "docs/experiments/exposure-input-manifest.json").read_text("utf-8"))
report = json.loads((ROOT / "docs/experiments/exposure-reference-result.json").read_text("utf-8"))
assert report["scope"] == "own_srgb_linear_exposure_reference_no_resolve_or_ocio_execution"
data = (ROOT / "experiments/output/exposure-inputs/opaque-srgb16-patches.png").read_bytes()
assert hashlib.sha256(data).hexdigest() == report["input_sha256"]
assert data[:8] == b"\x89PNG\r\n\x1a\n"
pos, payload, kinds = 8, [], []
while pos < len(data):
    size = struct.unpack_from(">I", data, pos)[0]
    kind, block = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + size]
    assert zlib.crc32(kind + block) == struct.unpack_from(">I", data, pos + 8 + size)[0]
    if kind == b"IHDR":
        assert struct.unpack(">IIBBBBB", block) == (1920, 1080, 16, 2, 0, 0, 0)
    if kind == b"sRGB":
        assert block == b"\0"
    if kind == b"IDAT":
        payload.append(block)
    kinds.append(kind.decode("ascii"))
    pos += size + 12
assert pos == len(data) and kinds[-1] == "IEND" and kinds.count("sRGB") == 1
rows, stride = zlib.decompress(b"".join(payload)), 1920 * 6 + 1
assert len(rows) == stride * 1080
for y in range(1080):
    assert rows[y * stride] == 0
    expected = b"".join(struct.pack(">3H", *manifest["samples"][(y // 270) * 4 + col]["encoded_rgb_u16"]) * 480
                        for col in range(4))
    assert rows[y * stride + 1:(y + 1) * stride] == expected
checks, max_error = 0, 0
assert [c["ev"] for c in report["cases"]] == [-1, 0, 1]
with localcontext() as context:
    context.prec = 50
    for case in report["cases"]:
        work_values = [value for sample in case["samples"] for value in sample["work_linear_rgb"]]
        assert case["work_range"] == [min(work_values), max(work_values)]
        path = ROOT / "experiments/output/exposure-reference" / case["preview"]["name"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == case["preview"]["sha256"]
        with Image.open(path) as preview:
            assert preview.size == (1920, 1080) and preview.mode == "RGB" and preview.info["srgb"] == 0
            assert len(case["samples"]) == 16
            for source, sample in zip(manifest["samples"], case["samples"]):
                assert source["id"] == sample["id"] and source["sample_xy"] == sample["sample_xy"]
                assert len(sample["work_linear_rgb"]) == 3
                expected_codes = []
                for code, actual in zip(source["encoded_rgb_u16"], sample["work_linear_rgb"]):
                    value = Decimal(code) / Decimal(65535)
                    linear = (value / Decimal("12.92") if value <= Decimal("0.04045") else
                              ((value + Decimal("0.055")) / Decimal("1.055")) ** Decimal("2.4"))
                    wanted = linear * (Decimal(2) ** case["ev"])
                    error = abs(float(wanted) - actual)
                    max_error = max(max_error, error)
                    assert error < 1e-15
                    display = min(Decimal(1), max(Decimal(0), wanted))
                    encoded = (Decimal("12.92") * display if display <= Decimal("0.0031308") else
                               Decimal("1.055") * (display ** (Decimal(1) / Decimal("2.4"))) - Decimal("0.055"))
                    expected_codes.append(int(encoded * Decimal(255) + Decimal("0.5")))
                    checks += 1
                assert sample["preview_rgb_u8"] == expected_codes
                assert preview.getpixel(tuple(sample["sample_xy"])) == tuple(expected_codes)
    wrong_encoded = min(Decimal(1), Decimal(manifest["samples"][5]["encoded_rgb_u16"][0]) * 2 / Decimal(65535))
    assert report["negative_control"]["sample_id"] == 5
    assert report["negative_control"]["wrong_operation"] == "multiply sRGB encoded value by 2 and clamp, then decode"
    wrong_expected = ((wrong_encoded + Decimal("0.055")) / Decimal("1.055")) ** Decimal("2.4")
    assert len(report["negative_control"]["wrong_work_linear_rgb"]) == 3
    for actual in report["negative_control"]["wrong_work_linear_rgb"]:
        assert abs(float(wrong_expected) - actual) < 1e-15
    assert report["negative_control"]["correct_plus1_work_linear_rgb"] == report["cases"][2]["samples"][5]["work_linear_rgb"]
assert checks == 144
assert report["cases"][2]["samples"][9]["work_linear_rgb"] == [2.0, 2.0, 2.0]
assert report["cases"][2]["samples"][9]["preview_rgb_u8"] == [255, 255, 255]
assert abs(report["negative_control"]["wrong_work_linear_rgb"][0] -
           report["negative_control"]["correct_plus1_work_linear_rgb"][0]) > 0.4
result = {"scope": "independent_decimal50_numeric_and_png_readback_not_resolve_validation",
          "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "input_full_grid_pixels_verified": True, "scalar_channels_checked": checks,
          "preview_centers_checked": 48, "max_float64_vs_decimal50_error": max_error,
          "superwhite_retained_in_work_table": True, "negative_control_distinguished": True}
(ROOT / "docs/experiments/exposure-reference-validation.json").write_text(json.dumps(result, indent=2) + "\n", "utf-8")
print(json.dumps(result))
