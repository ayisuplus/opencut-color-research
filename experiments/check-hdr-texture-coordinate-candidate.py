"""Post-hoc texture-coordinate hypothesis; table size and binding are unverified."""
import ast
import hashlib
import json
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
paths = [root / p for p in ["docs/experiments/resolve-hdr-near-zero-result.json",
    "docs/experiments/resolve-hdr-global-grid-result.json", "experiments/evaluate-hdr-domain-candidates.py"]]
texts = [p.read_text(encoding="utf8") for p in paths]
near, old = [json.loads(t) for t in texts[:2]]
tree = ast.parse(texts[2])
nodes = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name.startswith("bt709_")) or
         (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "bt709_threshold" for t in n.targets))]
ns = {"np": np}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(paths[2]), "exec"), ns)
decode, encode = ns["bt709_decode"], ns["bt709_encode"]
linear = decode(np.array(near["sample_RGB"]["near-zero"]))
assert np.array_equal(near["sample_RGB"]["near-zero"], old["sample_RGB"]["neutral-before"])
# Hypotheses, not values recovered from the host or from a native texture.
weights = np.array([0.2126, 0.7152, 0.0722])
q = np.log2(np.clip(linear @ weights / 0.18, 2.0 ** -8, 2.0 ** 8))
n = 1024
position = (q + 8) / 16 * n - 0.5
index = np.floor(position).astype(int)
fraction = position - index
observations = [(name, e, np.array(near["sample_RGB"][name])) for name, e in
    [("near-plus-large", 2.0**-10), ("near-minus-large", -2.0**-10),
     ("near-plus-small", 2.0**-14), ("near-minus-small", -2.0**-14)]]
observations += [("old-plus1", 1.0, np.array(old["sample_RGB"]["hdr-plus1"])),
                 ("old-minus1", -1.0, np.array(old["sample_RGB"]["hdr-minus1"]))]

def stats(a):
    return {"channels": int(a.size), "max_abs": float(np.abs(a).max()),
            "rmse": float(np.sqrt(np.mean(a**2)))}

rows = []
for table_kind, quantized in [("endpoints", False), ("endpoints", True), ("centers", False)]:
    alpha = np.round(fraction * 256) / 256 if quantized else fraction
    i0, i1 = np.clip(index, 0, n-1), np.clip(index+1, 0, n-1)
    table = -8 + 16 * (np.arange(n) / (n-1) if table_kind == "endpoints" else (np.arange(n)+0.5) / n)
    sampled_zero = table[i0] * (1-alpha) + table[i1] * alpha
    results = []
    for name, e, actual in observations:
        predicted = encode(linear * 2.0 ** (sampled_zero[:, None] - q[:, None] + e))
        assert np.isfinite(predicted).all()
        results.append({"name": name, "stored_gainjz": e, "predicted_RGB": predicted.tolist(),
                        "residual": stats(predicted-actual)})
    zero_prediction = encode(linear * 2.0 ** (sampled_zero[:, None] - q[:, None]))
    rows.append({"table": table_kind, "alpha_nearest_1_over_256": quantized,
                 "nonzero_results": results,
                 "zero_extrapolation_residual": stats(zero_prediction - np.array(near["sample_RGB"]["near-zero"]))})
result = {"scope": "post_hoc_texture_coordinate_hypothesis_on_existing_48_channels",
          "new_native_frames": 0, "texture_width_assumption": n, "linear_RGB_Y_weights_assumption": weights.tolist(),
          "working_Y_scale_assumption": "working second channel = 100 * weighted decoded RGB",
          "table_assumption": "global-only table is identity log coordinate plus E",
          "sampler_assumptions": "normalized coordinates, linear filtering, clamp addressing; optional nearest 8-bit alpha",
          "sources": [{"path": str(p.relative_to(root)).replace("\\", "/"),
                       "sha256_utf8_lf": hashlib.sha256(t.encode()).hexdigest()} for p,t in zip(paths,texts)],
          "rows": rows, "limits": ["N=1024 was hypothesized after observing the residual, not recovered or independently validated.",
            "No native texture contents, sampler descriptor, host upload, runtime kernel link or noise model.",
            "Ideal arithmetic except optional alpha quantization; not a PTX/GPU numeric emulator.",
            "The zero extrapolation is deliberately reported, not silently replaced with identity.",
            "Fixed 16-color nonnegative fixture only; no claim for arbitrary images, sRGB or full HDR controls."]}
out = root / "docs/experiments/hdr-texture-coordinate-candidate.json"
out.write_text(json.dumps(result, indent=2)+"\n", encoding="utf8", newline="\n")
print(json.dumps([{ "table": r["table"], "quantized": r["alpha_nearest_1_over_256"],
                    "errors": {v["name"]: v["residual"]["max_abs"] for v in r["nonzero_results"]}} for r in rows], indent=2))
