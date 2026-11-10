"""The circuit as KiCad reads it from the project schematic.

pico-step.kicad_sch and its sheets are built from the text drawing in
tsch/ (mise run sch). The tests check the netlist kicad-cli exports from
that file, which is exactly what the board is updated from.
"""

from __future__ import annotations

import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def schematic(tmp_path_factory) -> dict:
    """components: ref, value, footprint per part. nets: name and pins
    ("U5.21") of every connected net. no_connect: pins marked unused.
    pin_names: "U5.21" -> "VS"."""
    sch = ROOT / "pico-step.kicad_sch"
    if not sch.exists():
        pytest.fail("pico-step.kicad_sch is missing: run mise run sch")
    xml = tmp_path_factory.mktemp("netlist") / "net.xml"
    subprocess.run(
        ["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml",
         "-o", str(xml), str(sch)],
        check=True, capture_output=True,
    )
    root = ET.parse(xml).getroot()
    components = [
        {"ref": c.get("ref"), "value": c.findtext("value") or "",
         "footprint": c.findtext("footprint") or ""}
        for c in root.iter("comp")
    ]
    # Pin names come from the library parts: a node's pinfunction carries
    # the pin number as a suffix ("REFL_1").
    lib_pins = {
        (lp.get("lib"), lp.get("part")): {p.get("num"): p.get("name") or ""
                                          for p in lp.iter("pin")}
        for lp in root.iter("libpart")
    }
    part_pins = {}
    for c in root.iter("comp"):
        src = c.find("libsource")
        part_pins[c.get("ref")] = (
            {} if src is None else lib_pins.get((src.get("lib"), src.get("part")), {}))
    nets, no_connect, pin_names = [], [], {}
    for net in root.iter("net"):
        pins = []
        for node in net.iter("node"):
            pin = f"{node.get('ref')}.{node.get('pin')}"
            pins.append(pin)
            pin_names[pin] = part_pins.get(node.get("ref"), {}).get(node.get("pin"), "")
        # KiCad names the net of a pin marked unused "unconnected-(...)";
        # a pin left open without the mark is an ERC error instead.
        name = net.get("name") or ""
        if name.startswith("unconnected-"):
            no_connect.extend(pins)
        else:
            nets.append({"name": name, "pins": pins})
    return {"components": components, "nets": nets,
            "no_connect": no_connect, "pin_names": pin_names}
