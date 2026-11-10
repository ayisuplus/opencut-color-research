"""Read a fixed OCIO PE snapshot as bytes; never load or execute the target."""
import hashlib
import json
from pathlib import Path
import struct

import pefile


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "evidence/local/resolve-exposure-20261012"
TARGET = CASE / "targets/OpenColorIO_2_4.dll"
SEEDS = CASE / "analysis/ocio-renderer-seeds.json"
OUTPUT = CASE / "analysis/ocio-renderer-vtables.json"
EXPECTED_SHA = "a1658f7bbe6193ce34f9f6dd4beaf5820c19a2455758c91a9bdb6d2ba5444478"
SOURCE_SHA = "2831d2547d133b326c6e9a09726ceeb7fe46f997"
SOURCE_ROOT = "https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/" + SOURCE_SHA
NAMES = ("ECLinearRenderer", "ECVideoRenderer", "ECLogarithmicRenderer")
SLOT_NAMES = ("deleting_destructor", "apply", "isDynamic", "hasDynamicProperty",
              "getDynamicProperty", "updateData")


def inspect():
    data = TARGET.read_bytes()
    seed_bytes = SEEDS.read_bytes()
    seeds = json.loads(seed_bytes.decode("utf-8-sig"))
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA or seeds["sha256"] != digest:
        raise RuntimeError("Target or seed hash does not match the fixed case")
    pe = pefile.PE(data=data, fast_load=True)
    if pe.FILE_HEADER.Machine != 0x8664 or pe.OPTIONAL_HEADER.Magic != 0x20B:
        raise RuntimeError("Only AMD64 PE32+ is supported")
    image_base = pe.OPTIONAL_HEADER.ImageBase
    if int(seeds["image_base"], 16) != image_base:
        raise RuntimeError("Seed preferred image base mismatch")

    def section_at(rva, size=1):
        return next((s for s in pe.sections
                     if 0 <= rva - s.VirtualAddress <= s.SizeOfRawData - size), None)

    def read(rva, size):
        section = section_at(rva, size)
        if section is None:
            raise ValueError("Read is outside file-backed section bytes")
        offset = section.PointerToRawData + rva - section.VirtualAddress
        result = data[offset:offset + size]
        if len(result) != size:
            raise ValueError("Short file-backed read")
        return result

    def raw_to_rva(offset, size):
        for section in pe.sections:
            if 0 <= offset - section.PointerToRawData <= section.SizeOfRawData - size:
                return section.VirtualAddress + offset - section.PointerToRawData
        raise ValueError("Raw location is not file-backed section data")

    def address(rva):
        section = section_at(rva)
        if section is None:
            raise ValueError("Address is outside file-backed section bytes")
        return {"rva": hex(rva), "preferred_va": hex(image_base + rva),
                "raw_offset": section.PointerToRawData + rva - section.VirtualAddress,
                "section": section.Name.rstrip(b"\0").decode("ascii")}

    def references(needle):
        cursor = 0
        while True:
            cursor = data.find(needle, cursor)
            if cursor < 0:
                return
            yield cursor
            cursor += 1

    def type_name(rva):
        name = read(rva + 16, min(256, section_at(rva + 16).SizeOfRawData
                                - (rva + 16 - section_at(rva + 16).VirtualAddress)))
        if b"\0" not in name:
            raise ValueError("Unterminated type name")
        return name.split(b"\0", 1)[0].decode("ascii")

    def hierarchy(rva):
        signature, attributes, count, array_rva = struct.unpack("<4I", read(rva, 16))
        if signature != 0 or not 1 <= count <= 16:
            raise ValueError("Unsupported class hierarchy descriptor")
        bases = []
        for bcd_rva in struct.unpack("<" + "I" * count, read(array_rva, count * 4)):
            td, contained, mdisp, pdisp, vdisp, flags, chd = struct.unpack(
                "<IIiiiII", read(bcd_rva, 28))
            bases.append({"descriptor": address(bcd_rva), "type_descriptor": address(td),
                          "type_name": type_name(td), "contained_bases": contained,
                          "pmd": {"mdisp": mdisp, "pdisp": pdisp, "vdisp": vdisp},
                          "attributes": flags, "class_descriptor_rva": hex(chd)})
        return {"address": address(rva), "signature": signature, "attributes": attributes,
                "base_class_array": address(array_rva), "bases": bases}

    runtime_functions = {}
    directory = pe.OPTIONAL_HEADER.DATA_DIRECTORY[3]
    for offset in range(0, directory.Size - 11, 12):
        begin, end, unwind = struct.unpack("<3I", read(directory.VirtualAddress + offset, 12))
        if begin:
            runtime_functions[begin] = {"begin_rva": hex(begin), "end_rva": hex(end),
                                        "unwind_rva": hex(unwind)}

    renderers = []
    for name in NAMES:
        seed = next(s for s in seeds["matches"] if s["pattern"] == name)
        concrete = [s for s in seed["locations"] if s["string"].startswith(".?AV" + name + "@")]
        if len(concrete) != 1:
            raise RuntimeError("Expected one concrete renderer TypeDescriptor seed")
        seed = concrete[0]
        pattern_rva = int(seed["rva"], 16)
        name_rva = pattern_rva - seed["string"].index(name)
        type_rva = name_rva - 16
        if raw_to_rva(seed["raw_offset"], len(name)) != pattern_rva:
            raise RuntimeError("Seed raw/RVA mapping mismatch")
        if type_name(type_rva) != seed["string"]:
            raise RuntimeError("Seed type name does not match target bytes")
        td_vft, spare = struct.unpack("<2Q", read(type_rva, 16))
        if spare != 0 or section_at(td_vft - image_base) is None:
            raise RuntimeError("Unsupported TypeDescriptor prefix")
        locators = []
        for reference_raw in references(struct.pack("<I", type_rva)):
            try:
                col_rva = raw_to_rva(reference_raw - 12, 24)
                fields = struct.unpack("<6I", read(col_rva, 24))
                signature, offset, cd_offset, td, chd, self_rva = fields
                if col_rva % 4 or signature != 1 or td != type_rva or self_rva != col_rva:
                    continue
                chain = hierarchy(chd)
                base_names = [b["type_name"] for b in chain["bases"]]
                if base_names[0] != seed["string"] or not any("ECRendererBase@" in b for b in base_names):
                    continue
                tables = []
                for prefix_raw in references(struct.pack("<Q", image_base + col_rva)):
                    vtable_rva = raw_to_rva(prefix_raw + 8, len(SLOT_NAMES) * 8)
                    table_section = section_at(vtable_rva)
                    if vtable_rva % 8 or table_section.Characteristics & 0x20000000:
                        continue
                    slots = []
                    for index in range(16):
                        function_va = struct.unpack("<Q", read(vtable_rva + index * 8, 8))[0]
                        function_rva = function_va - image_base
                        section = section_at(function_rva)
                        if section is None or not section.Characteristics & 0x20000000:
                            break
                        slots.append({"index": index, "inferred_method": SLOT_NAMES[index] if index < 6 else None,
                                      "pointer": address(vtable_rva + index * 8),
                                      "function": address(function_rva),
                                      "prefix_bytes": read(function_rva, 16).hex(),
                                      "pdata_exact_entry": runtime_functions.get(function_rva)})
                    if len(slots) != len(SLOT_NAMES):
                        continue
                    tables.append({"address": address(vtable_rva), "col_pointer": address(vtable_rva - 8),
                                   "slots": slots, "apply_candidate": slots[1]["function"]})
                locators.append({"address": address(col_rva), "raw_bytes": read(col_rva, 24).hex(),
                                 "signature": signature, "offset": offset, "cd_offset": cd_offset,
                                 "self_rva": hex(self_rva), "hierarchy": chain, "vtables": tables})
            except (ValueError, struct.error, UnicodeDecodeError):
                continue
        if len(locators) != 1 or locators[0]["offset"] != 0 or locators[0]["cd_offset"] != 0 or len(locators[0]["vtables"]) != 1:
            raise RuntimeError("Did not recover exactly one primary locator and six-slot vtable for " + name)
        renderers.append({"class": name, "type_name": seed["string"],
                          "seed_pattern_address": address(pattern_rva), "name_address": address(name_rva),
                          "type_descriptor": address(type_rva), "type_descriptor_vft_preferred_va": hex(td_vft),
                          "locators": locators})
    report = {
        "scope": "read_only_msvc_x64_rtti_renderer_entry_candidates", "target": str(TARGET),
        "sha256": digest, "seed_sha256": hashlib.sha256(seed_bytes).hexdigest(),
        "image_base": hex(image_base), "va_kind": "preferred_image_base_plus_rva_not_runtime_address",
        "executes_target": False, "loads_target": False, "modifies_target": False,
        "pefile_version": pefile.__version__, "binary_facts": "validated_type_name_COL_self_RVA_hierarchy_and_executable_vtable_slots",
        "method_assignment": "candidate_from_official_v2_4_0_single_inheritance_virtual_order_not_decompiled",
        "apply_slot_index": 1, "apply_slot_byte_offset": 8,
        "ocio_source_ref": {"tag": "v2.4.0", "commit": SOURCE_SHA,
                            "opcpu": SOURCE_ROOT + "/src/OpenColorIO/Op.h#L34-L51",
                            "renderer_base": SOURCE_ROOT + "/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp#L20-L41",
                            "linear": SOURCE_ROOT + "/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp#L131-L140",
                            "video": SOURCE_ROOT + "/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp#L341-L350",
                            "logarithmic": SOURCE_ROOT + "/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp#L548-L557"},
        "col_layout_reference": "https://github.com/llvm/llvm-project/blob/llvmorg-20.1.8/clang/lib/CodeGen/MicrosoftCXXABI.cpp#L3903-L3916",
        "limitations": ["Official source virtual order does not prove identical vendor build implementation",
                        "No runtime use of these classes by any Resolve exposure control has been established",
                        "An executable-section pointer and .pdata match are not decompilation or behavior validation"],
        "renderers": renderers,
    }
    pe.close()
    return report


if __name__ == "__main__":
    result = inspect()
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "sha256": result["sha256"], "apply_candidates": [
        {"class": r["class"], **r["locators"][0]["vtables"][0]["apply_candidate"]}
        for r in result["renderers"]]}, ensure_ascii=False))
