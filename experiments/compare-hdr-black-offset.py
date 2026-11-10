"""Compare four native frames for the single observed Black Offset change."""
import hashlib
import json
import os
from pathlib import Path

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2
import numpy as np

root = Path(__file__).resolve().parents[1]
case = root / "evidence/local/resolve-hdr-black-offset-20261013"
def read(path):
    return json.loads(path.read_text(encoding="utf8"))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
plan_path = case / "analysis/frozen-pixel-plan.json"
receipt_path = case / "analysis/native-black-offset-render-results.json"
plan, receipt = read(plan_path), read(receipt_path)
final_path = case / "runtime/pixel-finalize.json"
final = json.loads(read(final_path)["content"][0]["text"])["result"]
assert receipt["failure"] is None and len(receipt["completed"]) == 4
assert len(set(receipt["owned_ids"])) == 4 and set(final["owned_ids"]) == set(receipt["owned_ids"])
assert {r["job_id"] for r in receipt["completed"]} == set(receipt["owned_ids"])
assert set(receipt["owned_ids"]).isdisjoint(j["JobId"] for j in plan["expected"]["jobs"])
assert final["original_13_jobs_full_snapshot_match"] and final["job_count"] == 17
assert final["neutral"] and final["saved_exported"] and final["all_owned_complete"]
assert final["settings_clip_timecode_match"] and not final["rendering"]
pixels, measured, frames = {}, {}, []
for row, frozen in zip(receipt["completed"], plan["rows"]):
    assert all(row[k] == frozen[k] for k in frozen)
    assert row["status"] == {"JobStatus": "Complete", "CompletionPercentage": 100}
    assert row["job_id"] in receipt["owned_ids"] and sha(Path(row["grade"])) == row["sha256"]
    name = row["name"]
    m = read(case / "analysis" / (name + "-measured.json"))
    raw = Path(row["file"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == m["image_sha256"]
    assert m["opencv_crosscheck_exact"] and m["crosscheck_channels"] == 6220800
    rgb = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_UNCHANGED)[:, :, ::-1].astype("<f4")
    assert hashlib.sha256(rgb.tobytes()).hexdigest() == m["rgb_pixels_sha256"]
    pixels[name], measured[name] = rgb, m
    frames.append({"name": name, "status": row["status"], "grade_sha256": row["sha256"],
                   "EXR_sha256": m["image_sha256"], "RGB_sha256": m["rgb_pixels_sha256"]})
assert measured["offset-before"]["rgb_pixels_sha256"] == plan["reference_RGB_hashes"]["cold-rec709-plus1"]
assert pixels["offset-before"].tobytes() == pixels["offset-before-repeat"].tobytes()
assert measured["offset-neutral-restored"]["rgb_pixels_sha256"] == plan["reference_RGB_hashes"]["cold-rec709-neutral"]
delta = pixels["offset-after"].astype(np.float64) - pixels["offset-before"].astype(np.float64)
sample_delta = np.array([s["rgb"] for s in measured["offset-after"]["samples"]]) - np.array([s["rgb"] for s in measured["offset-before"]["samples"]])
fixture = root / "experiments/output/exposure-inputs/opaque-srgb16-patches.png"
fixture_sha256 = sha(fixture)
assert fixture_sha256 == "2daa68135e4ac8c0585fb33630ce5d69a735640799b82a8173caafbfc8d9f09f"
result = {"scope": "Fixed Rec709 native Global +1, UI Black Offset 0 to 0.010 response",
    "new_native_frames": 4, "native_frames_cumulative": 36,
    "fixture_sha256_verified_after_render": fixture_sha256,
    "plan_sha256": sha(plan_path), "receipt_sha256": sha(receipt_path), "finalize_sha256": sha(final_path),
    "frames": frames, "channels_per_frame": 6220800,
    "manual_OpenCV_crosscheck_exact": True, "original_13_jobs_preserved": True,
    "fresh_baseline_matches_previous_Rec709_plus1": True, "baseline_repeat_RGB_identical": True,
    "neutral_restore_matches_frozen_RGB": True,
    "after_minus_before": {"changed_channels": int(np.count_nonzero(delta)),
        "max_abs": float(np.abs(delta).max()), "min": float(delta.min()), "max": float(delta.max()),
        "rmse": float(np.sqrt(np.mean(delta ** 2)))},
    "sample_RGB": {name: [s["rgb"] for s in m["samples"]] for name, m in measured.items()},
    "sample_after_minus_before": sample_delta.tolist(),
    "limits": ["One UI Black Offset point at one stored Global exposure and Rec709 condition.",
        "Inputs are exact native grades independently validated before replay; no per-frame post-render DRX readback.",
        "No new palette menu witness after applying grades; neutral state had Use Timeline witness.",
        "Does not identify full exposure formula or explain previous sRGB residuals.",
        "EXR values are measured code values, not assumed physical linear-light quantities."]}
out = root / "docs/experiments/resolve-hdr-black-offset-result.json"
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8", newline="\n")
print(json.dumps({"response": result["after_minus_before"], "samples": result["sample_after_minus_before"]}, indent=2))
