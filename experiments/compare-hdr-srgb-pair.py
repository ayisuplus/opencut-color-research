"""Measure the fixed sRGB minus/zero/plus sequence and its native readbacks."""
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2
import numpy as np

case, previous_case, output_path = map(Path, sys.argv[1:4])
receipt_path = case / "analysis/native-srgb-pair-render-results.json"
receipt = json.loads(receipt_path.read_text(encoding="utf8"))
plan_path = case / "analysis/frozen-srgb-pair-grid-plan.json"
plan = json.loads(plan_path.read_text(encoding="utf8"))
rows = receipt["completed"]
assert receipt["failure"] is None and receipt["restoration"]["restored"] and receipt["restoration"]["source_full_snapshot_match"]
assert len(rows) == len(set(receipt["owned_ids"])) == 5
assert {r["job_id"] for r in rows} == set(receipt["owned_ids"])
assert set(receipt["owned_ids"]).isdisjoint(plan["existing_jobs"])
assert {j["JobId"] for j in receipt["existing_jobs_snapshot"]} == set(plan["existing_jobs"])
assert [r["name"] for r in rows] == [r["name"] for r in plan["sequence"]]
for row, planned in zip(rows, plan["sequence"]):
    for key in ["condition", "stored_gainjz", "apply_grade", "grade_sha256"]:
        assert row[key] == planned[key]
finalize_path = case / "runtime/pair-finalize-copy-result.json"
finalize = json.loads(json.loads(finalize_path.read_text(encoding="utf8"))[-1]["result"]["content"][0]["text"])["result"]
assert finalize["existing_jobs_snapshot_match"] and finalize["neutral"] and finalize["saved_exported"]


def load(row, directory):
    data = json.loads((directory / "analysis" / (row["name"] + "-measured.json")).read_text(encoding="utf8"))
    raw = Path(row["file"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == data["image_sha256"]
    assert data["opencv_crosscheck_exact"] and data["crosscheck_channels"] == 6220800
    rgb = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_UNCHANGED)[:, :, ::-1].astype("<f4")
    assert hashlib.sha256(rgb.tobytes()).hexdigest() == data["rgb_pixels_sha256"]
    return data, rgb


measured, pixels = {}, {}
for row in rows:
    assert row["status"] == {"JobStatus": "Complete", "CompletionPercentage": 100}
    measured[row["name"]], pixels[row["name"]] = load(row, case)


def compare(a, b):
    delta = b.astype(np.float64) - a.astype(np.float64)
    return {"channels": int(a.size), "RGB_bytes_identical": a.tobytes() == b.tobytes(),
        "changed_channels": int(np.count_nonzero(delta)), "max_abs_difference": float(np.abs(delta).max()),
        "RMSE": float(np.sqrt(np.mean(delta ** 2)))}


previous_path = previous_case / "analysis/native-cold-context-render-results.json"
assert hashlib.sha256(previous_path.read_bytes()).hexdigest() == plan["prior_render_receipt_sha256"]
previous = json.loads(previous_path.read_text(encoding="utf8"))["completed"]
old = {r["name"]: load(r, previous_case)[1] for r in previous if r["name"] in ["cold-srgb-neutral", "cold-srgb-plus1"]}
comparisons = {"zero_vs_neutral": compare(pixels["pair-srgb-neutral"], pixels["pair-srgb-zero"]),
    "rec709_restored_vs_neutral": compare(pixels["pair-srgb-neutral"], pixels["pair-rec709-restored"]),
    "previous_srgb_neutral": compare(old["cold-srgb-neutral"], pixels["pair-srgb-neutral"]),
    "previous_srgb_plus1": compare(old["cold-srgb-plus1"], pixels["pair-srgb-plus1"])}
validation_path = case / "analysis/independent-srgb-pair-drx-validation.json"
validation = json.loads(validation_path.read_text(encoding="utf8"))
assert validation["render_receipt"]["sha256"] == hashlib.sha256(receipt_path.read_bytes()).hexdigest()
assert validation["summary"]["grades"] == 3 and all(validation["summary"].values())
readbacks = {r["name"]: r for r in rows if r["native_readback"]}
assert len(validation["checks"]) == len(readbacks) == 3
assert {c["name"] for c in validation["checks"]} == set(readbacks)
for check in validation["checks"]:
    row = readbacks[check["name"]]
    assert check["source"]["sha256"] == row["grade_sha256"]
    assert check["readback"]["sha256"] == row["native_readback"]["sha256"]
    assert hashlib.sha256(Path(row["native_readback"]["file"]).read_bytes()).hexdigest() == check["readback"]["sha256"]
    assert check["exact_expected_Global_gainjz"] and check["gainjz_semantic_value"] == row["stored_gainjz"]
    assert not check["non_timestamp_semantic_leaf_changes"]
    for body in check["bodies"]:
        assert body["canonical_Parameter_serializations_all_identical"] and body["node_identities_equal"]
        assert body["VersionBody_canonical_excluding_lastmodtime_equal"]
        assert all(body["readback"]["strict_metrics"][k] == 0 for k in ["unknown", "issues", "required_missing", "oneof_multiple_members", "unconsumed_bytes"])
samples = {name: [s["rgb"] for s in data["samples"]] for name, data in measured.items()}
result = {"scope": plan["scope"], "native_version": "21.1.1.10", "fixture_sha256": plan["fixture"]["sha256"],
    "plan_sha256": hashlib.sha256(plan_path.read_bytes()).hexdigest(),
    "render_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
    "existing_job_count": len(plan["existing_jobs"]), "new_job_count": 5, "existing_jobs_snapshot_match": True,
    "source_full_snapshot_restored": True, "frames": [{"name": r["name"], "stored_gainjz": r["stored_gainjz"],
        "condition": r["condition"], "grade_sha256": r["grade_sha256"], "status": r["status"],
        "EXR_sha256": measured[r["name"]]["image_sha256"], "RGB_sha256": measured[r["name"]]["rgb_pixels_sha256"]} for r in rows],
    "manual_OpenCV_crosscheck_channels_per_frame": 6220800, "comparisons": comparisons, "sample_RGB": samples,
    "readbacks": [{"name": c["name"], "gainjz": c["gainjz_semantic_value"], "wire_present": c["gainjz_wire_present"],
        "zero_presence_normalized": c["zero_presence_normalized"], "DRX_sha256": c["readback"]["sha256"]} for c in validation["checks"]],
    "readback_validation_sha256": hashlib.sha256(validation_path.read_bytes()).hexdigest(),
    "candidate_inputs": {"srgb": {"gray_sample_ids": list(range(10)), "sample_RGB": {
        "neutral-before": samples["pair-srgb-neutral"], "hdr-minus1": samples["pair-srgb-minus1"],
        "hdr-zero": samples["pair-srgb-zero"], "hdr-plus1": samples["pair-srgb-plus1"]}}},
    "limits": ["Project close/reopen is not an application/GPU/cache cold start.",
        "Stored minus/zero/plus values have no new 005 UI witness.", "005 HDR palette menu settings have no direct UI witness.",
        "A canonical zero default and pixel equality do not make an HDR grade identical to the no-HDR branch.",
        "Fixed candidate decoding domains do not prove the native internal formula."]}
output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8", newline="\n")
print(json.dumps(comparisons, indent=2))
