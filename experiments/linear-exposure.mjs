// Research probe: nonnegative SDR sRGB gray only; not a Resolve reconstruction.
// Transfer functions: https://www.w3.org/TR/css-color-4/#color-conversion-code
import assert from "node:assert/strict";

const encodeSrgb = (linear) =>
  linear <= 0.0031308
    ? 12.92 * linear
    : 1.055 * linear ** (1 / 2.4) - 0.055;
const decodeSrgb = (encoded) =>
  encoded <= 0.04045
    ? encoded / 12.92
    : ((encoded + 0.055) / 1.055) ** 2.4;

const inputLinear = 0.18;
const inputSrgb = encodeSrgb(inputLinear);
const correctLinear = inputLinear * 2 ** 1;
const correctSrgb = encodeSrgb(correctLinear);
const wrongSrgb = Math.min(1, inputSrgb * 2);
const wrongLinear = decodeSrgb(wrongSrgb);

// Fixed analytical values also computed with Python Decimal at 50-digit precision.
assert.ok(Math.abs(inputSrgb - 0.46135612950044165) < 1e-14);
assert.equal(inputLinear * 2 ** 0, 0.18);
assert.equal(correctLinear, 0.36);
assert.ok(Math.abs(correctSrgb - 0.6342527406021729) < 1e-14);
assert.ok(Math.abs(decodeSrgb(correctSrgb) - 0.36) < 1e-12);
assert.ok(wrongLinear > correctLinear * 2);

console.log(JSON.stringify({
  experiment: "one_stop_exposure_domain_comparison",
  input: { linear: inputLinear, srgb: inputSrgb },
  correct: { linear: correctLinear, srgb: correctSrgb, exposure_ev: 1 },
  deliberately_wrong: {
    linear: wrongLinear,
    srgb: wrongSrgb,
    equivalent_linear_exposure_ev: Math.log2(wrongLinear / inputLinear),
  },
  checks_passed: 6,
  evidence_scope: "scalar_srgb_math_only",
  resolve_verified: false,
  opencut_integrated: false,
}, null, 2));
