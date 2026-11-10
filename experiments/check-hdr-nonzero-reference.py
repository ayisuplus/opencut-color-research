"""Post-hoc conditional reference transfer across already observed exposure levels."""
import ast
import hashlib
import json
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
paths = [root / p for p in [
    "docs/experiments/resolve-hdr-near-zero-result.json",
    "docs/experiments/resolve-hdr-global-grid-result.json",
    "experiments/evaluate-hdr-domain-candidates.py"]]
texts = [p.read_text(encoding="utf8") for p in paths]
near, old = [json.loads(t) for t in texts[:2]]
tree = ast.parse(texts[2])
nodes = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name.startswith("bt709_")) or
         (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "bt709_threshold" for t in n.targets))]
ns = {"np": np}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(paths[2]), "exec"), ns)
decode, encode = ns["bt709_decode"], ns["bt709_encode"]
samples = {k: np.array(v, dtype=np.float64) for k, v in near["sample_RGB"].items()}
zero = samples["near-zero"]
assert np.array_equal(zero, np.array(old["sample_RGB"]["neutral-before"]))
e = near["pairs"]["small"]["epsilon"]
# Estimate 48 channel references only from the smaller nonzero pair.
b_plus = decode(samples["near-plus-small"]) / 2.0 ** e
b_minus = decode(samples["near-minus-small"]) / 2.0 ** -e
b = (b_plus + b_minus) / 2

def stats(a):
    return {"channels": int(a.size), "max_abs": float(np.abs(a).max()),
            "rmse": float(np.sqrt(np.mean(a ** 2)))}

levels = [("near-plus-large", near["pairs"]["large"]["epsilon"], samples["near-plus-large"]),
          ("near-minus-large", -near["pairs"]["large"]["epsilon"], samples["near-minus-large"]),
          ("old-plus1", 1.0, np.array(old["sample_RGB"]["hdr-plus1"])),
          ("old-minus1", -1.0, np.array(old["sample_RGB"]["hdr-minus1"]))]
rows = []
for name, level, actual in levels:
    # np.where evaluates the unused power branch on tiny negative channels.
    # Keep the frozen signed linear branch; do not clip these values.
    with np.errstate(invalid="ignore"):
        predicted = encode(b * 2.0 ** level)
    assert np.isfinite(predicted).all()
    residual = predicted - actual
    baseline_residual = encode(decode(zero) * 2.0 ** level) - actual
    rows.append({"name": name, "stored_gainjz": level, "predicted_RGB": predicted.tolist(),
                 "residual_RGB": residual.tolist(), "baseline_residual": stats(baseline_residual),
                 "strata": {label: stats(residual[ids]) for label, ids in
                    [("all", list(range(16))), ("gray", list(range(10))), ("color", list(range(10, 16)))]}})
with np.errstate(invalid="ignore"):
    extrapolated_zero = encode(b)
assert np.isfinite(extrapolated_zero).all()
result = {"scope": "post_hoc_conditional_reference_check_not_formula_identification",
          "new_native_frames": 0, "estimated_channel_references": 48,
          "construction": "B = (decode709(F(+e))/2**e + decode709(F(-e))/2**(-e))/2; e=2**-14",
          "prediction": "encode709(B * 2**stored_gainjz)",
          "sources": [{"path": str(p.relative_to(root)).replace("\\", "/"),
                       "sha256_utf8_lf": hashlib.sha256(t.encode()).hexdigest()} for p, t in zip(paths, texts)],
          "inferred_B_RGB": b.tolist(), "B_plus_minus_disagreement": stats(b_plus - b_minus),
          "inferred_zero_extrapolation_error": stats(extrapolated_zero - zero), "predictions": rows,
          "inferred_B_negative_channels": int(np.count_nonzero(b < 0)), "inferred_B_min": float(b.min()),
          "limits": ["48 sample-dependent reference values are estimated; not a general pixel transform.",
                     "Target levels were already observed: post-hoc consistency, not blinded or prospective validation.",
                     "Only this nonnegative fixture and frozen Rec709 condition; not sRGB or arbitrary colors.",
                     "Negative and above-one values use the frozen candidate algebraic extension, not proof of ITU normative-domain behavior.",
                     "No tolerance, exact equivalence, internal branch, continuity limit, or physical EV conclusion.",
                     "The extrapolated zero does not equal observed zero; this is not a complete exposure formula."]}
out = root / "docs/experiments/hdr-nonzero-reference-result.json"
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8", newline="\n")
print(json.dumps({"disagreement": result["B_plus_minus_disagreement"],
                  "zero_extrapolation_error": result["inferred_zero_extrapolation_error"],
                  "predictions": [{"name": r["name"], "baseline": r["baseline_residual"], "conditional": r["strata"]["all"]} for r in rows]}, indent=2))
