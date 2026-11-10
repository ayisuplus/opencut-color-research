"""Compare the six fixed native frames after independent EXR reader checks."""
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

render_path, manifest_path, output_path, plot_path = map(Path, sys.argv[1:5])
rendered = json.loads(render_path.read_text(encoding="utf8"))["completed"]
manifest = json.loads(manifest_path.read_text(encoding="utf8"))
names = ["neutral-before", "hdr-minus1", "hdr-zero", "hdr-plus1",
         "hdr-zero-repeat", "neutral-restored"]
assert [r["name"] for r in rendered] == names
frames, measured = {}, {}
for entry in rendered:
    name = entry["name"]
    report = json.loads((render_path.parent / (name + "-measured.json")).read_text(encoding="utf8"))
    assert report["opencv_crosscheck_exact"] and report["crosscheck_channels"] == 6220800
    path = Path(entry["file"])
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == report["image_sha256"]
    rgb = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_UNCHANGED)[:, :, ::-1]
    assert rgb.shape == (1080, 1920, 3) and np.isfinite(rgb).all()
    assert hashlib.sha256(rgb.astype("<f4").tobytes()).hexdigest() == report["rgb_pixels_sha256"]
    frames[name], measured[name] = rgb, report
baseline = frames["neutral-before"]
comparisons = {}
for name in names[1:]:
    delta = frames[name].astype(np.float64) - baseline
    comparisons[name] = {"exact_numeric_equal": bool(np.array_equal(frames[name], baseline)),
                         "changed_channels": int(np.count_nonzero(delta)),
                         "max_abs_delta": float(np.max(np.abs(delta)))}
samples = {name: np.array([s["rgb"] for s in measured[name]["samples"]]) for name in names}
gray_ids = [s["id"] for s in manifest["samples"] if len(set(s["encoded_rgb_u16"])) == 1]
candidate_errors = {}
for name, exponent in (("hdr-minus1", -1), ("hdr-zero", 0), ("hdr-plus1", 1)):
    candidate_errors[name] = float(np.max(np.abs(samples[name] - samples["neutral-before"] * 2.0 ** exponent)))
result = {"scope": "fixed_PNG16_native_HDR_Global_UI_three_levels_not_full_algorithm",
          "whole_frame_channels": int(baseline.size), "sample_channels": 48,
          "frames": {name: {k: measured[name][k] for k in ["image_sha256", "rgb_pixels_sha256", "opencv_crosscheck_exact"]} for name in names},
          "whole_frame_range": {name: {"min": float(frames[name].min()), "max": float(frames[name].max()),
                                       "negative_channels": int(np.count_nonzero(frames[name] < 0)),
                                       "over_one_channels": int(np.count_nonzero(frames[name] > 1))} for name in names},
          "vs_no_HDR_neutral_grade": comparisons,
          "zero_repeat_exact_RGB_bytes": measured["hdr-zero"]["rgb_pixels_sha256"] == measured["hdr-zero-repeat"]["rgb_pixels_sha256"],
          "candidate_EXR_code_times_2_power_level_max_error_48_samples": candidate_errors,
          "candidate_limit": "Tests direct EXR channel scaling only; does not test physical linear-light exposure without a confirmed transform domain.",
          "gray_sample_ids": gray_ids, "sample_RGB": {name: samples[name].tolist() for name in names}}
output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
fig, ax = plt.subplots(figsize=(7.5, 5))
x = samples["neutral-before"][gray_ids, 0]
for name, label in (("hdr-minus1", "Global -1.00"), ("hdr-zero", "Global 0.00"), ("hdr-plus1", "Global +1.00")):
    ax.plot(x, samples[name][gray_ids, 0], marker="o", label=label)
ax.plot(x, x, linestyle="--", color="gray", label="No-HDR neutral grade")
ax.set(xlabel="Neutral EXR channel value (gray patch centers)", ylabel="Graded EXR R channel value",
       title="Native HDR Global: fixed PNG16 / Rec.709 (Scene) timeline")
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()
fig.savefig(plot_path, dpi=160)
plt.close(fig)
print(json.dumps({k: result[k] for k in ["vs_no_HDR_neutral_grade", "zero_repeat_exact_RGB_bytes", "candidate_EXR_code_times_2_power_level_max_error_48_samples"]}, indent=2))
