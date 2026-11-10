"""Check equal-input and superposition constraints on the inferred B table."""
import hashlib
import itertools
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = [root / p for p in (
    "docs/experiments/resolve-hdr-near-zero-result.json",
    "docs/experiments/hdr-nonzero-reference-result.json",
    "docs/experiments/resolve-hdr-global-grid-result.json",
    "docs/experiments/exposure-input-manifest.json",
    "experiments/evaluate-hdr-domain-candidates.py")]
texts = [p.read_text(encoding="utf8") for p in paths]
near, reference, old, manifest = [json.loads(t) for t in texts[:4]]
reference_sources = {s["path"]: s["sha256_utf8_lf"] for s in reference["sources"]}
for i in (0, 2, 4):
    assert hashlib.sha256(texts[i].encode()).hexdigest() == reference_sources[str(paths[i].relative_to(root)).replace("\\", "/")]
assert hashlib.sha256(texts[4].encode()).hexdigest() == "1c824137901be048cda536abf9f620fb7f577cec55ed71971f221f224f9bc479"
zero, b = near["sample_RGB"]["near-zero"], reference["inferred_B_RGB"]
assert zero == old["sample_RGB"]["neutral-before"]
assert len(zero) == len(b) == len(manifest["samples"]) == 16
assert all(len(r) == 3 for r in zero + b)
e = near["pairs"]["small"]["epsilon"]
assert e == 2**-14
threshold = 1.099 * .018**.45 - .099

def decode(x):
    return x / 4.5 if x < threshold else ((x + .099) / 1.099)**(1 / .45)

def derive(samples, exposure):
    return [[decode(x) / 2**exposure for x in row] for row in samples]

sp = derive(near["sample_RGB"]["near-plus-small"], e)
sm = derive(near["sample_RGB"]["near-minus-small"], -e)
op = derive(old["sample_RGB"]["hdr-plus1"], 1)
om = derive(old["sample_RGB"]["hdr-minus1"], -1)
old_b = [[(p + m) / 2 for p, m in zip(a, c)] for a, c in zip(op, om)]
assert max(abs(b[i][c] - (sp[i][c] + sm[i][c]) / 2) for i in range(16) for c in range(3)) < 1e-15
level = zero[6][0]
groups = []
for c in range(3):
    ids = [i for i, row in enumerate(zero) if row[c] == level]
    assert len(ids) == 4
    assert all(manifest["samples"][i]["encoded_rgb_u16"][c] == 35199 for i in ids)
    pairs = []
    for i, j in itertools.combinations(ids, 2):
        left, right = sorted([sp[i][c], sm[i][c]]), sorted([sp[j][c], sm[j][c]])
        pairs.append({"patch_ids": [i, j], "B_difference": b[j][c] - b[i][c],
            "small_plus_difference": sp[j][c] - sp[i][c], "small_minus_difference": sm[j][c] - sm[i][c],
            "old_pair_difference": old_b[j][c] - old_b[i][c],
            "two_estimate_spans_disjoint": left[1] < right[0] or right[1] < left[0]})
    spread = max(b[i][c] for i in ids) - min(b[i][c] for i in ids)
    groups.append({"channel": "RGB"[c], "input_code": level, "source_u16": 35199,
        "members": [{"patch_id": i, "input_RGB": zero[i], "B": b[i][c],
            "B_small_plus": sp[i][c], "B_small_minus": sm[i][c], "B_old_pair": old_b[i][c]} for i in ids],
        "B_range": spread, "scalar_minimax_error_lower_bound": spread / 2, "pairs": pairs})
additivity = []
for target, parts in ((13, [11, 12]), (14, [10, 12]), (15, [10, 11]), (6, [10, 11, 12])):
    assert all(zero[target][c] == sum(zero[p][c] for p in parts) for c in range(3))
    residual = [b[target][c] - sum(b[p][c] for p in parts) + (len(parts) - 1) * b[0][c] for c in range(3)]
    additivity.append({"target_patch": target, "primary_patches": parts,
        "affine_superposition_residual": residual, "max_abs": max(map(abs, residual))})
result = {"scope": "post_hoc_constraints_on_inferred_B_table_not_native_algorithm_identification",
    "new_native_frames": 0, "new_fitted_coefficients": 0,
    "sources": [{"path": str(p.relative_to(root)).replace("\\", "/"),
        "sha256_utf8_lf": hashlib.sha256(t.encode()).hexdigest()} for p, t in zip(paths, texts)],
    "same_channel_equal_input_groups": groups, "affine_superposition_checks": additivity,
    "old_pair_B_max_change": max(abs(b[i][c] - old_b[i][c]) for i in range(16) for c in range(3)),
    "limits": ["B already contains 48 sample-dependent estimates under the frozen BT709 candidate.",
        "Only exact scalar/affine explanations of this finite B table are tested.",
        "Two-estimate spans are not confidence intervals or measurement noise bounds.",
        "Color and patch position co-vary; color context is not isolated from spatial context.",
        "All active colored-patch inputs share one amplitude; arbitrary mixed colors remain untested.",
        "No proof of a native matrix, color space, luminance rule, or general pixel transform."]}
out = root / "docs/experiments/hdr-reference-context-result.json"
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8", newline="\n")
print(json.dumps({"same_input_B_ranges": {g["channel"]: g["B_range"] for g in groups},
    "affine_residuals": [r["max_abs"] for r in additivity], "old_pair_B_max_change": result["old_pair_B_max_change"]}))
