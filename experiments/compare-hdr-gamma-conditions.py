"""Measure the frozen seven-frame Gamma configuration contrast, without model fitting."""
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2
import numpy as np

case, previous_case, output_path = map(Path, sys.argv[1:4])
plan_path = case / "analysis/frozen-gamma-conditions-plan.json"
plan = json.loads(plan_path.read_text(encoding="utf8"))
receipt_path = case / "analysis/native-gamma-condition-render-results.json"
receipt = json.loads(receipt_path.read_text(encoding="utf8"))
rows = receipt["completed"]
assert len(rows) == len(receipt["owned_ids"]) == 7 and receipt["inherited_ids"] == []
assert [row["name"] for row in rows] == [row["name"] for row in plan["sequence"]]


def load(row, directory):
    measured = json.loads((directory / "analysis" / (row["name"] + "-measured.json")).read_text(encoding="utf8"))
    raw = Path(row["file"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == measured["image_sha256"]
    assert measured["opencv_crosscheck_exact"] and measured["crosscheck_channels"] == 6220800
    bgr = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    rgb = bgr[:, :, ::-1].astype("<f4")
    assert hashlib.sha256(rgb.tobytes()).hexdigest() == measured["rgb_pixels_sha256"]
    return measured, rgb


measured, pixels = {}, {}
for row in rows:
    assert row["status"] == {"JobStatus": "Complete", "CompletionPercentage": 100}
    measured[row["name"]], pixels[row["name"]] = load(row, case)


def compare(a, b):
    difference = b.astype(np.float64) - a.astype(np.float64)
    return {"channels": int(a.size), "RGB_bytes_identical": a.tobytes() == b.tobytes(),
            "changed_channels": int(np.count_nonzero(difference)),
            "max_abs_difference": float(np.abs(difference).max()),
            "RMSE": float(np.sqrt(np.mean(difference ** 2)))}


previous = json.loads((previous_case / "analysis/native-hdr-grid-render-results.json").read_text(encoding="utf8"))["completed"]
previous_pixels = {row["name"]: load(row, previous_case)[1] for row in previous}
cross_conditions = {level: compare(pixels["rec709-" + level], pixels["gamma24-" + level])
                    for level in ["neutral", "minus1", "plus1"]}
prior_pairs = {"rec709-neutral": "neutral-before", "rec709-minus1": "hdr-minus1", "rec709-plus1": "hdr-plus1"}
prior_comparison = {new: compare(previous_pixels[old], pixels[new]) for new, old in prior_pairs.items()}
conditions = plan["conditions"]
for group in ["project_settings", "timeline_settings"]:
    changed = [k for k in conditions["rec709"][group] if conditions["rec709"][group][k] != conditions["gamma24"][group][k]]
    assert changed == ["colorSpaceTimelineGamma"]
assert all(conditions["rec709"][k] == conditions["gamma24"][k] for k in ["clip_properties", "media_id", "timeline_item_id"])
color_keys = ["colorScienceMode", "colorSpaceInput", "colorSpaceInputGamma", "colorSpaceTimeline", "colorSpaceTimelineGamma", "colorSpaceOutput", "colorSpaceOutputGamma", "separateColorSpaceAndGamma", "useColorSpaceAwareGradingTools", "colorSpaceOutputToneMapping", "colorSpaceOutputGamutMapping", "timelineWorkingLuminance"]
samples = {name: [sample["rgb"] for sample in data["samples"]] for name, data in measured.items()}
readback = json.loads((case / "analysis/native-gamma-condition-drx-validation.json").read_text(encoding="utf8"))
assert readback["summary"]["grades"] == 4 and all(v for k, v in readback["summary"].items() if k != "grades")
result = {"scope": plan["scope"], "native_version": "21.1.1.10", "fixture_sha256": plan["fixture"]["sha256"],
    "frozen_plan_sha256": hashlib.sha256(plan_path.read_bytes()).hexdigest(),
    "render_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
    "frames": [{"name": row["name"], "condition": row["condition"], "stored_gainjz": row["stored_gainjz"],
        "status": row["status"], "EXR_sha256": measured[row["name"]]["image_sha256"],
        "RGB_sha256": measured[row["name"]]["rgb_pixels_sha256"], "grade_sha256": row["grade_sha256"],
        "readback_sha256": row["native_readback"]["sha256"] if row["native_readback"] else None} for row in rows],
    "manual_OpenCV_crosscheck_channels_per_frame": 6220800,
    "runtime_color_settings": {name: {k: value["project_settings"][k] for k in color_keys} for name, value in conditions.items()},
    "cross_condition_full_RGB": cross_conditions, "previous_003_full_RGB": prior_comparison,
    "neutral_restoration_full_RGB": compare(pixels["rec709-neutral"], pixels["rec709-restored"]),
    "native_Drx_validation": readback["summary"], "sample_RGB": samples,
    "candidate_inputs": {condition: {"gray_sample_ids": list(range(10)), "sample_RGB": {
        "neutral-before": samples[condition + "-neutral"], "hdr-minus1": samples[condition + "-minus1"],
        "hdr-plus1": samples[condition + "-plus1"]}} for condition in ["rec709", "gamma24"]},
    "limits": ["Configuration getters do not establish the actual HDR operation domain.",
        "The previous 003 palette Use Timeline witness is not a new 004 UI witness.",
        "Neutral frames use a no-HDR grade; no new HDR-zero frame was exported.",
        "Post-save/reload defaults differ from the runtime snapshots; this grid does not test that later state.",
        "A fixed PNG16 still, positive samples and one frame do not establish video or negative-input behavior."]}
output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8", newline="\n")
print(json.dumps({"cross_condition": cross_conditions, "previous_003": prior_comparison}, indent=2))
