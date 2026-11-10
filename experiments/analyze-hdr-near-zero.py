"""Measure finite paired near-zero response; do not infer an internal formula."""
import ast
import hashlib
import json
import os
from pathlib import Path

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2
import numpy as np

root = Path(__file__).resolve().parents[1]
case = root / "evidence/local/resolve-hdr-near-zero-20261013"
def read(p):
    return json.loads(p.read_text(encoding="utf8"))
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(a):
    return {"channels": int(a.size), "max_abs": float(np.abs(a).max()),
            "rmse": float(np.sqrt(np.mean(a ** 2)))}

plan_path = case / "analysis/frozen-near-zero-plan.json"
receipt_path = case / "analysis/native-near-zero-render-results.json"
validation_path = case / "analysis/independent-native-readback-validation.json"
plan, receipt, validation = read(plan_path), read(receipt_path), read(validation_path)
assert receipt["failure"] is None and len(receipt["completed"]) == 6
assert len(set(receipt["owned_ids"])) == 6
assert {r["job_id"] for r in receipt["completed"]} == set(receipt["owned_ids"])
assert set(receipt["owned_ids"]).isdisjoint(j["JobId"] for j in plan["expected"]["jobs"])
assert validation["summary"]["grades"] == 5 and all(validation["summary"].values())
assert validation["plan_sha256"] == sha(plan_path) and validation["receipt_sha256"] == sha(receipt_path)
checks = {r["name"]: r for r in validation["checks"]}
assert set(checks) == {r["name"] for r in plan["rows"] if r["readback"]}
final_path = case / "runtime/finalize.json"
final = json.loads(read(final_path)["content"][0]["text"])["result"]
assert final["neutral"] and final["saved_exported"] and final["old_jobs_full_match"]
assert final["job_count"] == 23 and final["all_owned_complete"] and final["settings_clip_timecode_match"]
assert set(final["owned_ids"]) == set(receipt["owned_ids"]) and not final["rendering"]
pixels, samples, frames = {}, {}, []
for row, frozen in zip(receipt["completed"], plan["rows"]):
    assert all(row[k] == frozen[k] for k in frozen)
    assert row["status"] == {"JobStatus": "Complete", "CompletionPercentage": 100}
    assert sha(Path(row["grade"])) == row["sha256"]
    name = row["name"]
    m = read(case / "analysis" / (name + "-measured.json"))
    raw = Path(row["file"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == m["image_sha256"]
    assert m["opencv_crosscheck_exact"] and m["crosscheck_channels"] == 6220800
    rgb = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_UNCHANGED)[:, :, ::-1].astype("<f4")
    assert hashlib.sha256(rgb.tobytes()).hexdigest() == m["rgb_pixels_sha256"]
    if row["readback"]:
        check = checks[name]
        assert check["source_sha256"] == row["sha256"]
        assert check["readback_sha256"] == row["native_readback"]["sha256"] == sha(Path(row["native_readback"]["file"]))
    pixels[name] = rgb
    samples[name] = np.array([s["rgb"] for s in m["samples"]], dtype=np.float64)
    frames.append({"name": name, "stored_gainjz": row["stored_gainjz"], "tools": row["tools"],
                   "status": row["status"], "RGB_sha256": m["rgb_pixels_sha256"],
                   "EXR_sha256": m["image_sha256"], "grade_sha256": row["sha256"]})
assert frames[0]["RGB_sha256"] == frames[-1]["RGB_sha256"] == plan["reference_neutral_RGB_sha256"]
model_path = root / "experiments/evaluate-hdr-domain-candidates.py"
tree = ast.parse(model_path.read_text(encoding="utf8"))
nodes = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name.startswith("bt709_")) or
         (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "bt709_threshold" for t in n.targets))]
ns = {"np": np}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(model_path), "exec"), ns)
zero, zero_s = pixels["near-zero"].astype(np.float64), samples["near-zero"]
pairs, halves = {}, {}
for scale in ["large", "small"]:
    e = plan["epsilon_" + scale]
    plus, minus = (pixels["near-" + sign + "-" + scale].astype(np.float64) for sign in ["plus", "minus"])
    ps, ms = (samples["near-" + sign + "-" + scale] for sign in ["plus", "minus"])
    center, half = (plus + minus) / 2 - zero, (plus - minus) / 2
    cs, hs = (ps + ms) / 2 - zero_s, (ps - ms) / 2
    halves[scale] = half
    models = {}
    for sign, level, actual in [("plus", e, ps), ("minus", -e, ms)]:
        predicted = ns["bt709_encode"](ns["bt709_decode"](zero_s) * 2.0 ** level)
        models[sign] = {"predicted_RGB": predicted.tolist(), "residual_RGB": (predicted - actual).tolist(),
                        "strata": {label: stats((predicted - actual)[ids]) for label, ids in
                                   [("all", list(range(16))), ("gray", list(range(10))), ("color", list(range(10, 16)))]}}
    pairs[scale] = {"epsilon": e, "center_minus_zero": stats(center), "half_difference": stats(half),
        "half_difference_over_epsilon": stats(half / e),
        "plus_minus_zero": stats(plus - zero), "minus_minus_zero": stats(minus - zero),
        "sample_center_minus_zero": cs.tolist(), "sample_half_difference": hs.tolist(),
        "sample_half_difference_over_epsilon": (hs / e).tolist(), "BT709_candidate": models}
    pairs[scale]["sample_strata"] = {label: {
        "center_minus_zero": stats(cs[ids]), "half_difference": stats(hs[ids]),
        "half_difference_over_epsilon": stats(hs[ids] / e)} for label, ids in
        [("all", list(range(16))), ("gray", list(range(10))), ("color", list(range(10, 16)))]}
    model_center = (np.array(models["plus"]["predicted_RGB"]) + np.array(models["minus"]["predicted_RGB"])) / 2 - zero_s
    pairs[scale]["BT709_candidate_center_minus_zero"] = stats(model_center)
    pairs[scale]["BT709_candidate_center_residual"] = stats(model_center - cs)
result = {"scope": plan["scope"], "new_native_frames": 6, "native_frames_cumulative": 42,
    "plan_sha256": sha(plan_path), "receipt_sha256": sha(receipt_path), "finalize_sha256": sha(final_path),
    "readback_validation_sha256": sha(validation_path), "frozen_model_source_sha256": sha(model_path),
    "fixture_sha256": plan["fixture"]["sha256"], "frames": frames,
    "initial_zero_and_final_neutral_match_frozen_RGB": True,
    "original_17_jobs_preserved": True, "manual_OpenCV_crosscheck_channels_per_frame": 6220800,
    "pairs": pairs, "H_large_minus_16_H_small": stats(halves["large"] - 16 * halves["small"]),
    "sample_RGB": {k: v.tolist() for k, v in samples.items()},
    "limits": plan["limits"] + ["Finite differences are arithmetic observations, not proven mathematical limits.",
        "No noise model, arbitrary tolerance, physical EV claim, or fitted parameters."]}
out = root / "docs/experiments/resolve-hdr-near-zero-result.json"
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8", newline="\n")
print(json.dumps({"pairs": {k: {f: v[f] for f in ["epsilon", "center_minus_zero", "half_difference", "plus_minus_zero", "minus_minus_zero"]} for k, v in pairs.items()}, "odd_scaling_mismatch": result["H_large_minus_16_H_small"]}, indent=2))
