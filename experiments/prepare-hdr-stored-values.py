"""Prepare private calibration copies; never call Resolve or label them UI-verified."""
import hashlib
import json
from pathlib import Path
import re
import struct
import zstandard

root = Path(__file__).resolve().parents[1]
case = root / "evidence/local/resolve-hdr-20261013"
source = case / "grades/human_global_plus1_1.1.1.drx"
data = source.read_bytes()
assert hashlib.sha256(data).hexdigest() == "7a661fbaed96a5408e649ac83737aa3ce7ffcf0a179d18ce0163ae5fc989c598"

def varint(raw, start):
    value = 0
    for shift in range(0, 70, 7):
        byte = raw[start]
        start += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, start
    raise ValueError("Invalid varint")

def encode_varint(value):
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return bytes(result)

key = b"\x08" + encode_varint(0x86000305) + b"\x12"
matches = list(re.finditer(rb"<Body>([0-9a-fA-F]+)</Body>", data))
assert len(matches) == 2
candidates = []
for match in matches:
    frame = bytes.fromhex(match[1].decode("ascii"))
    assert frame[:5] == b"\x81\x28\xb5\x2f\xfd"
    body = zstandard.ZstdDecompressor().decompress(frame[1:], max_output_size=1048576)
    if key not in body:
        continue
    assert body.count(key) == 1
    value_size, value_start = varint(body, body.index(key) + len(key))
    value = body[value_start:value_start + value_size]
    assert value[:2] == b"\x82\x01"  # ParamValueType HDR list, field 16.
    hdr_size, hdr_start = varint(value, 2)
    hdr = value[hdr_start:hdr_start + hdr_size]
    assert len(hdr) == hdr_size and hdr[0] == 10
    zone_size, zone_start = varint(hdr, 1)
    zone = hdr[zone_start:zone_start + zone_size]
    assert len(zone) == zone_size and zone_start + zone_size == len(hdr)
    prefix = b"\x0a\x06Global\x15"
    assert zone.startswith(prefix)
    offset = value_start + hdr_start + zone_start + len(prefix)
    assert struct.unpack_from("<f", body, offset)[0] == 1.003199815750122
    candidates.append((match, frame, body, offset))
assert len(candidates) == 1
match, frame, body, offset = candidates[0]
records = []
for name, stored in [("minus1", -1.0), ("zero", 0.0), ("plus1", 1.0)]:
    changed = body[:offset] + struct.pack("<f", stored) + body[offset + 4:]
    assert changed[:offset] == body[:offset] and changed[offset + 4:] == body[offset + 4:]
    packed = frame[:1] + zstandard.ZstdCompressor(level=3).compress(changed)
    output = data[:match.start(1)] + packed.hex().encode("ascii") + data[match.end(1):]
    path = case / "grades" / ("stored_global_" + name + ".drx")
    assert not path.exists()
    path.write_bytes(output)
    records.append({"path": path.relative_to(root).as_posix(), "stored_gainjz": stored, "sha256": hashlib.sha256(output).hexdigest(), "bytes": len(output), "body_sha256": hashlib.sha256(changed).hexdigest(), "UI_display_verified": False})
manifest = {"scope": "prepared_stored_Global_gainjz_calibration_values_not_yet_UI_verified", "source_sha256": hashlib.sha256(data).hexdigest(), "parameter_key": "0x86000305", "zone": "Global", "field": "gainjz", "float_byte_offset_in_body": offset, "only_changed_decompressed_bytes": [offset, offset + 4], "outer_grade_bytes_preserved": True, "other_body_bytes_preserved": True, "native_apply_attempted": False, "variants": records}
(case / "analysis/prepared-hdr-stored-values.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
print("Prepared three private stored-value calibration grades; UI mapping remains unverified.")
