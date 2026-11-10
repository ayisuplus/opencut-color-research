"""Offline exploratory cross-check of fixed input/output transfer functions."""
import ast
import hashlib
import json
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
model_path = root / "experiments/evaluate-hdr-domain-candidates.py"
model_text = model_path.read_text(encoding="utf8")
tree = ast.parse(model_text)
selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) or
            (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and
             t.id in {"bt709_threshold", "models"} for t in n.targets))]
namespace = {"np": np}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(model_path), "exec"), namespace)
models = namespace["models"]
sources = {
    "original_rec709": ("docs/experiments/resolve-hdr-global-grid-result.json", None),
    "srgb": ("docs/experiments/resolve-hdr-srgb-pair-result.json", "srgb"),
}
report = {"scope": "exploratory_fixed_asymmetric_transfer_grid_on_existing_samples",
          "prediction": "output_encode(input_decode(neutral) * 2**stored_gainjz)",
          "fitted_parameters": 0, "new_native_frames": 0,
          "model_source_sha256_utf8_lf": hashlib.sha256(model_text.encode()).hexdigest(),
          "conditions": {},
          "limits": ["Post hoc model search, not held-out validation or native algorithm identification.",
                     "Different input/output functions may fail neutrality; zero error is reported explicitly.",
                     "Uses existing nonnegative fixture samples only; no extra clipping or black offset.",
                     "Transfer definitions and extended-range caveats inherit the frozen model source."]}
for name, (relative, condition) in sources.items():
    source_text = (root / relative).read_text(encoding="utf8")
    source = json.loads(source_text)
    if condition:
        source = source["candidate_inputs"][condition]
    samples = source["sample_RGB"]
    x = np.array(samples["neutral-before"], dtype=np.float64)
    assert x.shape == (16, 3)
    observed = {e: np.array(samples[k], dtype=np.float64) for e, k in
                [(-1, "hdr-minus1"), (0, "hdr-zero"), (1, "hdr-plus1")] if k in samples}
    assert -1 in observed and 1 in observed
    rows = []
    for input_name, (decode, _) in models.items():
        for output_name, (_, encode) in models.items():
            errors = {}
            for level, actual in observed.items():
                predicted = encode(decode(x) * 2.0 ** level)
                residual = predicted - actual
                assert np.isfinite(residual).all()
                errors[str(level)] = {"max_abs": float(np.abs(residual).max()),
                                      "rmse": float(np.sqrt(np.mean(residual ** 2)))}
            rows.append({"input": input_name, "output": output_name, "errors": errors,
                         "identity_max_abs": float(np.abs(encode(decode(x)) - x).max()),
                         "nonzero_worst_max_abs": max(errors[str(e)]["max_abs"] for e in (-1, 1))})
    rows.sort(key=lambda r: r["nonzero_worst_max_abs"])
    report["conditions"][name] = {"source": relative,
        "source_sha256_utf8_lf": hashlib.sha256(source_text.encode()).hexdigest(),
        "observed_levels": sorted(observed), "models": rows}
output = root / "docs/experiments/hdr-asymmetric-domain-candidates.json"
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8", newline="\n")
print(json.dumps({k: v["models"][:3] for k, v in report["conditions"].items()}, indent=2))
