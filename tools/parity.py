#!/usr/bin/env python3
"""Compare the hand-placed schematic's netlist with tools/circuit.py.

The schematic is edited in the KiCad GUI, so it can drift from the
generator. Nets are compared as pin sets (names are ignored); a two-pin
passive drawn with its pins swapped shows up as a difference too.
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


def schematic_nets(sch: Path) -> dict[frozenset[str], str]:
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "net.xml"
        subprocess.run(
            ["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml",
             "-o", str(xml), str(sch)],
            check=True, capture_output=True,
        )
        tree = ET.parse(xml)
    nets = {}
    for net in tree.iter("net"):
        pins = frozenset(f"{n.get('ref')}.{n.get('pin')}" for n in net.iter("node"))
        if len(pins) > 1:
            nets[pins] = net.get("name")
    return nets


def generator_nets() -> dict[frozenset[str], str]:
    out = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "circuit.py")],
        check=True, capture_output=True, text=True,
    ).stdout
    return {frozenset(n["pins"]): n["name"] for n in json.loads(out)["nets"] if len(n["pins"]) > 1}


def main() -> int:
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
