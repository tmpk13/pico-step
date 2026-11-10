#!/usr/bin/env python3
"""Compare the hand-placed schematic's netlist with another description.

The schematic is edited in the KiCad GUI, so it can drift from the
generator. Nets are compared as pin sets (names are ignored); a two-pin
passive drawn with its pins swapped shows up as a difference too.

    parity.py              hand schematic against tools/circuit.py
    parity.py --tsch SCH   hand schematic against SCH, the KiCad schematic
                           built from the text drawing in tsch/; parts are
                           compared too (value, footprint, MPN)

Exits 1 when anything differs.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PART_FIELDS = ("value", "footprint", "MPN")


def export_netlist(sch: Path) -> ET.Element:
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "net.xml"
        subprocess.run(
            ["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml",
             "-o", str(xml), str(sch)],
            check=True, capture_output=True,
        )
        return ET.parse(xml).getroot()


def netlist_nets(root: ET.Element) -> dict[frozenset[str], str]:
    nets = {}
    for net in root.iter("net"):
        pins = frozenset(f"{n.get('ref')}.{n.get('pin')}" for n in net.iter("node"))
        if len(pins) > 1:
            nets[pins] = net.get("name")
    return nets


def netlist_parts(root: ET.Element) -> dict[str, dict[str, str]]:
    """Reference -> value, footprint and MPN of every placed part."""
    parts = {}
    for comp in root.iter("comp"):
        fields = {f.get("name"): f.text or "" for f in comp.iter("field")}
        parts[comp.get("ref")] = {
            "value": comp.findtext("value") or "",
            "footprint": comp.findtext("footprint") or "",
            "MPN": fields.get("MPN", ""),
        }
    return parts


def schematic_nets(sch: Path) -> dict[frozenset[str], str]:
    return netlist_nets(export_netlist(sch))


def part_differences(a: dict[str, dict[str, str]],
                     b: dict[str, dict[str, str]]) -> list[str]:
    """One line per reference missing on a side or per field that differs."""
    lines = []
    for ref in sorted(a.keys() | b.keys()):
        if ref not in b:
            lines.append(f"{ref}: only in the hand schematic")
        elif ref not in a:
            lines.append(f"{ref}: only in the tsch schematic")
        else:
            for field in PART_FIELDS:
                if a[ref][field] != b[ref][field]:
                    lines.append(f"{ref} {field}: hand {a[ref][field]!r}, "
                                 f"tsch {b[ref][field]!r}")
    return lines


def compare_tsch(tsch_sch: Path) -> int:
    hand = export_netlist(ROOT / "pico-step.kicad_sch")
    drawn = export_netlist(tsch_sch)
    a, b = netlist_nets(hand), netlist_nets(drawn)
    for pins in sorted(a.keys() - b.keys(), key=sorted):
        print(f"hand only: {a[pins]:28} {' '.join(sorted(pins))}")
    for pins in sorted(b.keys() - a.keys(), key=sorted):
        print(f"tsch only: {b[pins]:28} {' '.join(sorted(pins))}")
    parts = part_differences(netlist_parts(hand), netlist_parts(drawn))
    for line in parts:
        print(line)
    differences = len(a.keys() ^ b.keys())
    print(f"{len(a)} hand nets, {len(b)} tsch nets, {differences} net "
          f"differences, {len(parts)} part differences")
    return 1 if differences or parts else 0


def generator_nets() -> dict[frozenset[str], str]:
    out = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "circuit.py")],
        check=True, capture_output=True, text=True,
    ).stdout
    return {frozenset(n["pins"]): n["name"] for n in json.loads(out)["nets"] if len(n["pins"]) > 1}


def main() -> int:
    if sys.argv[1:2] == ["--tsch"]:
        return compare_tsch(Path(sys.argv[2]))
    sch = schematic_nets(ROOT / "pico-step.kicad_sch")
    gen = generator_nets()
    only_sch = sorted((sch[k], sorted(k)) for k in sch.keys() - gen.keys())
    only_gen = sorted((gen[k], sorted(k)) for k in gen.keys() - sch.keys())
    for name, pins in only_sch:
        print(f"schematic only: {name:24} {' '.join(pins)}")
    for name, pins in only_gen:
        print(f"circuit.py only: {name:23} {' '.join(pins)}")
    print(f"{len(sch)} schematic nets, {len(gen)} generator nets, "
          f"{len(only_sch) + len(only_gen)} differences")
    return 1 if only_sch or only_gen else 0


if __name__ == "__main__":
    sys.exit(main())
