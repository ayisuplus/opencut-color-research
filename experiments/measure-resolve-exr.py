"""Measure this experiment's uncompressed RGB float scanline EXR independently."""
import json
import hashlib
import os
from pathlib import Path
import struct
import sys

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2
import numpy as np

image_path, manifest_path, output_path = map(Path, sys.argv[1:4])
raw = image_path.read_bytes()
assert struct.unpack_from("<II", raw) == (20000630, 2)
position = 8
attributes = {}

def cstring(data, start):
    end = data.index(0, start)
    return data[start:end].decode("ascii"), end + 1

while raw[position]:
    name, position = cstring(raw, position)
    kind, position = cstring(raw, position)
    size = struct.unpack_from("<I", raw, position)[0]
    position += 4
    attributes[name] = (kind, raw[position:position + size])
    position += size
position += 1
assert attributes["compression"] == ("compression", b"\x00")
assert attributes["lineOrder"] == ("lineOrder", b"\x00")
assert struct.unpack("<iiii", attributes["dataWindow"][1]) == (0, 0, 1919, 1079)
channel_data = attributes["channels"][1]
channel_position = 0
channels = []
while channel_data[channel_position]:
    name, channel_position = cstring(channel_data, channel_position)
    pixel_type, linear, x_sampling, y_sampling = struct.unpack_from("<iB3xii", channel_data, channel_position)
    channel_position += 16
    assert pixel_type == 2 and x_sampling == y_sampling == 1
    channels.append(name)
assert channels == ["B", "G", "R"]
assert struct.unpack("<ii", attributes["framesPerSecond"][1]) == (30, 1)

opencv = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
assert opencv is not None and opencv.shape == (1080, 1920, 3) and opencv.dtype == np.float32
manual_bgr = np.empty((1080, 1920, 3), dtype=np.float32)
for y in range(1080):
    offset = struct.unpack_from("<Q", raw, position + y * 8)[0]
    row_y, byte_count = struct.unpack_from("<ii", raw, offset)
    assert row_y == y and byte_count == 1920 * 3 * 4
    planes = np.frombuffer(raw, dtype="<f4", count=1920 * 3, offset=offset + 8).reshape(3, 1920)
    manual_bgr[y] = planes.T
assert np.isfinite(manual_bgr).all()
assert manual_bgr.astype("<f4").tobytes() == opencv.astype("<f4").tobytes()
rgb_pixels_sha256 = hashlib.sha256(manual_bgr[:, :, ::-1].astype("<f4").tobytes()).hexdigest()
manifest = json.loads(manifest_path.read_text(encoding="utf8"))
samples = []
for sample in manifest["samples"]:
    x, y = sample["sample_xy"]
    measured = manual_bgr[y, x, ::-1].astype(np.float64)
    encoded = np.array(sample["encoded_rgb_u16"], dtype=np.float64) / 65535
    linear = np.array(sample["realized_linear_rgb"], dtype=np.float64)
    samples.append({"id": sample["id"], "rgb": measured.tolist(), "max_error_encoded": float(np.max(np.abs(measured - encoded))), "max_error_linear": float(np.max(np.abs(measured - linear)))})
result = {"scope": "fixed_PNG16_to_EXR_RGBFloat_measurements", "image_sha256": hashlib.sha256(raw).hexdigest(), "rgb_pixels_sha256": rgb_pixels_sha256, "rgb_pixel_bytes": manual_bgr.nbytes, "channels": channels, "sample_channels": len(samples) * 3, "opencv_crosscheck_exact": True, "crosscheck_channels": manual_bgr.size, "opencv_version": cv2.__version__, "max_error_encoded": max(s["max_error_encoded"] for s in samples), "max_error_linear": max(s["max_error_linear"] for s in samples), "samples": samples}
output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
print(json.dumps({k: v for k, v in result.items() if k != "samples"}, indent=2))
