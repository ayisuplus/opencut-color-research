"""Read only selected PE snapshots; report imports/exports, not executable behavior."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import struct

import pefile

root = Path(__file__).resolve().parents[1]
case = root / "evidence/local/resolve-exposure-20261012"
manifest = json.loads((case / "analysis/target-manifest.json").read_text("utf-8-sig"))
results = []
for target in manifest:
    path = Path(target["Snapshot"])
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != target["Sha256"]:
        raise RuntimeError("Snapshot hash changed: " + path.name)
    pe = pefile.PE(str(path), fast_load=True)
    if pe.FILE_HEADER.Machine != 0x8664 or pe.OPTIONAL_HEADER.Magic != 0x20b:
        raise RuntimeError("Research reader supports only AMD64 PE32+")

    def read_backed(rva, size):
        section = pe.get_section_by_rva(rva)
        if size < 0 or section is None or not 0 <= rva - section.VirtualAddress <= section.SizeOfRawData - size:
            raise RuntimeError("RVA window is not wholly backed by one file section")
        data = pe.get_data(rva, size)
        if len(data) != size:
            raise RuntimeError("Short file-backed RVA read")
        return data

    def read_name(rva, limit):
        section = pe.get_section_by_rva(rva)
        if section is None:
            raise RuntimeError("Name RVA is not in a file section")
        available = section.SizeOfRawData - (rva - section.VirtualAddress)
        if available <= 0:
            raise RuntimeError("Name RVA has no file-backed bytes")
        data = read_backed(rva, min(limit, available))
        if b"\0" not in data:
            raise RuntimeError("Name has no terminator within research window")
        return data.split(b"\0", 1)[0].decode("ascii")

    pe.parse_data_directories(directories=[
        pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],
        pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT"],
        pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"],
    ])
    warnings = pe.get_warnings()
    descriptor_modules = []
    raw_ocio_symbols = []
    descriptor_directory = pe.OPTIONAL_HEADER.DATA_DIRECTORY[1]
    if not 0 < descriptor_directory.Size <= 65536 or descriptor_directory.Size % 20:
        raise RuntimeError("Import descriptor directory has unsupported size")
    descriptor_terminated = False
    for offset in range(0, descriptor_directory.Size, 20):
        descriptor = struct.unpack("<IIIII", read_backed(descriptor_directory.VirtualAddress + offset, 20))
        if not any(descriptor):
            descriptor_terminated = True
            break
        name = read_name(descriptor[3], 256)
        descriptor_modules.append({"module": name, "original_first_thunk": hex(descriptor[0]),
                                   "first_thunk": hex(descriptor[4])})
        if "OpenColorIO" in name:
            if descriptor[0] == 0:
                raise RuntimeError("OCIO lookup with zero OriginalFirstThunk is unsupported")
            for index in range(4096):
                thunk = struct.unpack("<Q", read_backed(descriptor[0] + index * 8, 8))[0]
                if thunk == 0:
                    break
                if thunk & (1 << 63):
                    if thunk & 0x7fffffffffff0000:
                        raise RuntimeError("Ordinal import has nonzero reserved bits")
                    symbol = "ordinal:" + str(thunk & 0xffff)
                else:
                    if thunk & 0x7fffffff80000000:
                        raise RuntimeError("Name import has nonzero reserved bits")
                    symbol = read_name(thunk + 2, 512)
                raw_ocio_symbols.append(symbol)
            else:
                raise RuntimeError("OCIO symbol table exceeds research bound")
    if not descriptor_terminated:
        raise RuntimeError("Import directory has no all-zero terminator within declared size")
    imports = []
    for kind in ("DIRECTORY_ENTRY_IMPORT", "DIRECTORY_ENTRY_DELAY_IMPORT"):
        for module in getattr(pe, kind, []):
            symbols = [entry.name.decode("ascii", "replace") if entry.name
                       else "ordinal:" + str(entry.ordinal) for entry in module.imports]
            imports.append({"kind": kind, "module": module.dll.decode("ascii", "replace"),
                            "count": len(symbols), "symbols": symbols})
    exports = [{"name": entry.name.decode("ascii", "replace") if entry.name else None,
                "rva": hex(entry.address), "ordinal": entry.ordinal}
               for entry in getattr(getattr(pe, "DIRECTORY_ENTRY_EXPORT", None), "symbols", [])]
    related = [module for module in imports if re.search("OpenColorIO|OpenCL|cuda", module["module"], re.I)]
    exposure_exports = [entry for entry in exports if re.search("Exposure|CDLTransform|ColorSpaceTransform", entry["name"] or "")]
    results.append({"name": path.name, "sha256": digest,
                    "machine": hex(pe.FILE_HEADER.Machine),
                    "image_base": hex(pe.OPTIONAL_HEADER.ImageBase),
                    "sections": [{"name": section.Name.rstrip(b"\0").decode("ascii", "replace"),
                                  "rva": hex(section.VirtualAddress),
                                  "raw_offset": section.PointerToRawData,
                                  "raw_bytes": section.SizeOfRawData} for section in pe.sections],
                    "imports": imports, "export_count": len(exports),
                    "parser_warnings": warnings,
                    "parsed_import_coverage": "partial" if warnings else "not_flagged_by_parser",
                    "raw_import_descriptors": descriptor_modules,
                    "raw_ocio_import_symbols": raw_ocio_symbols,
                    "exposure_related_exports": exposure_exports})
    print(json.dumps({"target": path.name, "machine": hex(pe.FILE_HEADER.Machine),
                      "import_module_count": len(imports),
                      "raw_descriptor_module_count": len(descriptor_modules),
                      "raw_ocio_modules": [entry["module"] for entry in descriptor_modules
                                           if "OpenColorIO" in entry["module"]],
                      "parser_warning_count": len(warnings),
                      "raw_ocio_symbol_count": len(raw_ocio_symbols),
                      "color_imports": [{"module": module["module"], "count": module["count"]}
                                        for module in related],
                      "export_count": len(exports),
                      "exposure_export_count": len(exposure_exports)}))
    pe.close()

report = {"scope": "read_only_pe_headers_imports_exports",
          "pefile_version": importlib.metadata.version("pefile"), "targets": results,
          "executes_target": False, "exposure_control_behavior_verified": False}
(case / "analysis/pe-inventory.json").write_text(json.dumps(report, indent=2), "utf-8")
