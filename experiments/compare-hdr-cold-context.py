"""Compare the fixed eight-frame close/reopen and grade replay experiment."""
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2
import numpy as np

case, previous_case, output_path = map(Path, sys.argv[1:4])
receipt_path = case / "analysis/native-cold-context-render-results.json"
receipt = json.loads(receipt_path.read_text(encoding="utf8"))
plan_path = case / "analysis/frozen-cold-context-grid-plan.json"
plan = json.loads(plan_path.read_text(encoding="utf8"))
rows = receipt["completed"]
assert receipt["failure"] is None and receipt["restoration"]["restored"]
assert len(rows) == len(set(receipt["owned_ids"])) == 8
assert [r["name"] for r in rows] == [r["name"] for r in plan["sequence"]]
assert {r["job_id"] for r in rows} == set(receipt["owned_ids"])
for row, planned in zip(rows, plan["sequence"]):
    for key in ["condition", "stored_gainjz", "apply_grade", "grade_sha256"]:
        assert row[key] == planned[key]


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
            "changed_channels": int(np.count_nonzero(delta)),
            "max_abs_difference": float(np.abs(delta).max()),
            "RMSE": float(np.sqrt(np.mean(delta ** 2)))}


pairs = [("cold-rec709-neutral", "cold-srgb-neutral"),
    ("cold-rec709-neutral", "cold-rec709-restored"),
    ("cold-rec709-plus1", "cold-srgb-plus1"),
    ("cold-srgb-plus1", "cold-srgb-plus1-replay"),
    ("cold-rec709-plus1", "cold-rec709-plus1-return"),
    ("cold-rec709-plus1-return", "cold-rec709-plus1-replay")]
comparisons = [{"a": a, "b": b, **compare(pixels[a], pixels[b])} for a, b in pairs]
validation_path = case / "analysis/independent-cold-context-drx-validation.json"
validation = json.loads(validation_path.read_text(encoding="utf8"))
assert validation["render_receipt"]["sha256"] == hashlib.sha256(receipt_path.read_bytes()).hexdigest()
readbacks = {r["name"]: r for r in rows if r["native_readback"]}
assert len(validation["checks"]) == len(readbacks) == 5
assert {check["name"] for check in validation["checks"]} == set(readbacks)
for check in validation["checks"]:
    assert check["source"]["sha256"] == readbacks[check["name"]]["grade_sha256"]
    assert check["readback"]["sha256"] == readbacks[check["name"]]["native_readback"]["sha256"]
    assert check["exact_expected_Global_gainjz"] and check["gainjz_cardinality"] == 1
    assert not check["non_timestamp_semantic_leaf_changes"]
    for body in check["bodies"]:
        assert body["raw_Parameter_serializations_all_identical"] and body["canonical_Parameter_serializations_all_identical"]
        assert body["HDR_scalar_presence_defaults_identical"] and body["node_identities_equal"]
        assert body["readback_hdr_branch_counts"]["17"] == body["readback_hdr_branch_counts"]["18"] == 0
        assert all(body["readback"]["strict_metrics"][k] == 0 for k in ["unknown", "issues", "required_missing", "oneof_multiple_members", "unconsumed_bytes"])
        assert body["readback"]["dynamic"]["initialized"] and not body["readback"]["dynamic"]["initialization_errors"]
        assert body["readback"]["dynamic"]["consumed_bytes"] == body["readback"]["decompressed_bytes"]
previous = json.loads((previous_case / "analysis/native-hdr-grid-render-results.json").read_text(encoding="utf8"))["completed"]
old = {r["name"]: load(r, previous_case)[1] for r in previous if r["name"] in ["neutral-before", "hdr-plus1"]}
prior = {"neutral": compare(old["neutral-before"], pixels["cold-rec709-neutral"]),
         "plus1": compare(old["hdr-plus1"], pixels["cold-rec709-plus1"])}
result = {"scope": plan["scope"], "native_version": "21.1.1.10",
    "fixture_sha256": plan["fixture"]["sha256"],
    "plan_sha256": hashlib.sha256(plan_path.read_bytes()).hexdigest(),
    "render_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
    "readback_validation": {"count": 5, "exact_Global_gainjz": 1.0,
        "all_Parameter_bytes_and_HDR_presence_defaults_identical_to_source": True,
        "validation_sha256": hashlib.sha256(validation_path.read_bytes()).hexdigest(),
        "validator_script_sha256": validation["validator_script"]["sha256"]},
    "frames": [{"name": row["name"], "condition": row["condition"], "stored_gainjz": row["stored_gainjz"],
        "apply_grade": row["apply_grade"], "status": row["status"],
        "EXR_sha256": measured[row["name"]]["image_sha256"],
        "RGB_sha256": measured[row["name"]]["rgb_pixels_sha256"], "grade_sha256": row["grade_sha256"],
        "readback_sha256": row["native_readback"]["sha256"] if row["native_readback"] else None} for row in rows],
    "manual_OpenCV_crosscheck_channels_per_frame": 6220800,
    "comparisons": comparisons, "previous_003_comparison": prior,
    "sample_RGB": {name: [sample["rgb"] for sample in data["samples"]] for name, data in measured.items()},
    "candidate_inputs": {condition: {"gray_sample_ids": list(range(10)),
        "sample_RGB": {"neutral-before": [s["rgb"] for s in measured["cold-" + condition + "-neutral"]["samples"]],
                       "hdr-plus1": [s["rgb"] for s in measured["cold-" + condition + "-plus1"]["samples"]]}}
        for condition in ["rec709", "srgb"]},
    "source_full_snapshot_restored": receipt["restoration"]["source_full_snapshot_match"],
    "limits": ["Only stored +1 and no-HDR neutral; no new HDR-zero or negative UI calibration.",
        "005 palette menu settings have no direct UI witness.",
        "Close/reopen and replay history are recorded actions; small differences are not uniquely attributed.",
        "A getter configuration and output relationship do not establish native HDR internal formulas."]}
output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8", newline="\n")
print(json.dumps({"comparisons": comparisons, "previous_003": prior}, indent=2))
