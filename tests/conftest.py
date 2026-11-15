"""The circuit as KiCad reads it from each board's schematic.

The project is a stack of boards. Each board folder (mcu, encoder,
driver) holds tsch/project.toml, whose name gives the board's files:
<folder>/<name>.kicad_sch, built from the folder's text drawing by mise run
sch, and <folder>/<name>.kicad_pcb. The tests check the netlist kicad-cli
exports from each schematic, which is exactly what the board is updated
from.
"""

from __future__ import annotations

import re
import subprocess
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BOARDS = sorted(p.parent.parent.name for p in ROOT.glob("*/tsch/project.toml"))
STACK_SHEET = ROOT / "stack" / "stack.tsch"
# The one-board layout every board's .kicad_pcb started as a copy of.
SINGLE_BOARD = ROOT / "pico-step.kicad_pcb"


def board_file(board: str, suffix: str) -> Path:
    """<board>/<project name><suffix>, e.g. mcu/pico-step-mcu.kicad_pcb."""
    manifest = tomllib.loads((ROOT / board / "tsch" / "project.toml").read_text())
    return ROOT / board / f"{manifest['name']}{suffix}"


def stack_refs() -> set[str]:
    """References on the stack sheet, which every board carries."""
    return set(re.findall(r"^\[part\.(\w+)\]", STACK_SHEET.read_text(), re.M))


def uncut_copy(board: str) -> bool:
    """True while the board is still a byte-for-byte copy of the one-board
    layout: it then holds every part of the stack, not its own."""
    path = board_file(board, ".kicad_pcb")
    return SINGLE_BOARD.exists() and path.read_bytes() == SINGLE_BOARD.read_bytes()


def load_netlist(sch: Path, xml: Path) -> dict:
    """components: ref, value, footprint per part. nets: name and pins
    ("U5.21") of every connected net. no_connect: pins marked unused.
    pin_names: "U5.21" -> "VS"."""
    if not sch.exists():
        pytest.fail(f"{sch.relative_to(ROOT)} is missing: run mise run sch")
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


@pytest.fixture(scope="session")
def schematics(tmp_path_factory) -> dict[str, dict]:
    """Board folder name -> its netlist (see load_netlist)."""
    tmp = tmp_path_factory.mktemp("netlist")
    return {b: load_netlist(board_file(b, ".kicad_sch"), tmp / f"{b}.xml")
            for b in BOARDS}


@pytest.fixture(params=BOARDS)
def board(request) -> str:
    return request.param


@pytest.fixture
def schematic(schematics, board) -> dict:
    """The netlist of one board; tests using it run once per board."""
    return schematics[board]
