"""Test explicit mathematical exposure candidates against the fixed native samples."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

source_path, output_path = map(Path, sys.argv[1:3])
source = json.loads(source_path.read_text(encoding="utf8"))
condition = sys.argv[3] if len(sys.argv) == 4 else None
if condition is not None:
    source = source["candidate_inputs"][condition]
x = np.array(source["sample_RGB"]["neutral-before"], dtype=np.float64)
assert x.shape == (16, 3) and np.all(x >= 0)
gray_ids = source["gray_sample_ids"]
color_ids = [i for i in range(16) if i not in gray_ids]

def srgb_decode(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)

def srgb_encode(v):
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * v ** (1 / 2.4) - 0.055)

bt709_threshold = 1.099 * 0.018 ** 0.45 - 0.099

def bt709_decode(v):
    return np.where(v < bt709_threshold, v / 4.5, ((v + 0.099) / 1.099) ** (1 / 0.45))

def bt709_encode(v):
    return np.where(v < 0.018, v * 4.5, 1.099 * v ** 0.45 - 0.099)

models = {
    "direct_EXR_channel": (lambda v: v, lambda v: v),
    "pure_gamma_2_4": (lambda v: np.sign(v) * np.abs(v) ** 2.4, lambda v: v ** (1 / 2.4)),
    "OCIO_video_1_83": (lambda v: np.sign(v) * np.abs(v) ** 1.83, lambda v: v ** (1 / 1.83)),
    "sRGB_piecewise": (srgb_decode, srgb_encode),
    "BT709_rounded_constants_Colour_inverse": (bt709_decode, bt709_encode),
}
reports = {}
observations = [(-1, "hdr-minus1"), (1, "hdr-plus1")]
if "hdr-zero" in source["sample_RGB"]:
    observations.insert(1, (0, "hdr-zero"))
observations = [(level, frame) for level, frame in observations if frame in source["sample_RGB"]]
assert observations
for name, (decode, encode) in models.items():
    linear = decode(x)
    assert np.max(np.abs(encode(linear) - x)) < 1e-12
    levels = {}
    for exponent, frame in observations:
        actual = np.array(source["sample_RGB"][frame], dtype=np.float64)
        predicted = encode(linear * 2.0 ** exponent)
        error = predicted - actual
        strata = {}
        for label, ids in (("all", list(range(16))), ("gray", gray_ids), ("color", color_ids)):
            residual = error[ids]
            strata[label] = {"channels": int(residual.size), "max_abs_error": float(np.abs(residual).max()),
                             "RMSE": float(np.sqrt(np.mean(residual ** 2)))}
        active = (x > 0) & (actual > 0)
        effective = np.log2(decode(actual)[active] / linear[active])
        worst = np.unravel_index(np.argmax(np.abs(error)), error.shape)
        levels[str(exponent)] = {"errors": strata,
            "worst_sample": {"id": int(worst[0]), "channel": "RGB"[worst[1]],
                             "predicted": float(predicted[worst]), "native": float(actual[worst])},
            "effective_level_in_assumed_decoded_domain": {"channels": int(effective.size),
                "min": float(effective.min()), "max": float(effective.max()), "mean": float(effective.mean())}}
    reports[name] = {"levels": levels}
    if "hdr-minus1" in source["sample_RGB"] and "hdr-plus1" in source["sample_RGB"]:
        minus = np.array(source["sample_RGB"]["hdr-minus1"], dtype=np.float64)
        plus = np.array(source["sample_RGB"]["hdr-plus1"], dtype=np.float64)
        paired_active = (x > 0) & (minus > 0) & (plus > 0)
        decoded_minus, decoded_plus = decode(minus), decode(plus)
        ratios = decoded_plus[paired_active] / decoded_minus[paired_active]
        reports[name]["paired_nonzero_levels"] = {
            "active_channels": int(paired_active.sum()), "plus_over_minus_min": float(ratios.min()),
            "plus_over_minus_max": float(ratios.max()), "max_abs_error_from_4": float(np.abs(ratios - 4).max()),
            "common_reference_max_abs_delta": float(np.abs(2 * decoded_minus[paired_active] - 0.5 * decoded_plus[paired_active]).max())}
result = {"scope": "fixed_48_native_EXR_code_samples_candidate_domain_comparison",
    "source_sha256": hashlib.sha256(source_path.read_text(encoding="utf8").encode("utf8")).hexdigest(),
    "source_hash_encoding": "UTF-8 text with LF newlines",
    "prediction": "encode(decode(neutral_EXR_channel) * 2**stored_gainjz)",
    "evaluation_dtype": "float64 predictions versus native float32 samples",
    "fitted_parameters": 0, "BT709_decode_threshold": bt709_threshold, "models": reports,
    "sources": ["https://www.w3.org/TR/2026/CRD-css-color-4-20261009/",
        "https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.709-6-201506-I!!PDF-E.pdf",
        "https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/rgb/transfer_functions/itur_bt_601.py",
        "https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/592a122b37467c3376f2387fbbdbe7b571fad39f/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpData.h"],
    "limits": ["No candidate establishes the actual native input decoding or HDR operation domain.",
        "BT709 positive formula is algebraically extended above linear 1 without clipping; that range is outside the cited ITU table's normative domain.",
        "The BT709 inverse threshold follows the fixed Colour implementation; rounded standard constants have a small join gap.",
        "Effective levels are arithmetic in each assumed decoding model, not measured physical EV.",
        "No alpha, negative-input, temporal, or HDR/Log/RAW verification."]}
if condition is not None:
    result["condition"] = condition
    result["observed_stored_levels"] = [level for level, _ in observations]
    result["neutral_reference"] = "No-HDR grade; not a new native HDR-zero observation."
output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8", newline="\n")
print(json.dumps({name: {"max_errors": {level: row["errors"]["all"]["max_abs_error"] for level, row in report["levels"].items()},
                        "nonzero_pair_ratio_error_from_4": report.get("paired_nonzero_levels", {}).get("max_abs_error_from_4")}
                  for name, report in reports.items()}, indent=2))
