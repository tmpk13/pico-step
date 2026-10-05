"""Reference designator checks.

Parts on the ESP32-C5 antenna path carry an `_rf` suffix so they stand out
during placement and ordering. The schematic and board are edited in the
KiCad GUI as well as generated, so their reference sets are compared with
the generator to catch a rename made in only one place.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RF_NETS = {"ANT_2G", "ANT_5G", "RF_2G", "RF_5G", "RF_COM", "RF_ANT"}


@pytest.fixture(scope="module")
def circuit() -> dict:
    out = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "circuit.py")],
        check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out)


def refs_in(path: Path) -> set[str]:
    text = path.read_text()
    # Schematic instances carry the placed reference; the Reference property
    # in its embedded library symbols is only the prefix ("C", "R").
    if path.suffix == ".kicad_sch":
        return set(re.findall(r'\(reference "([^"#][^"]*)"\)', text))
    return set(re.findall(r'\(property "Reference" "([^"#][^"]*)"', text))


def test_rf_suffix_matches_rf_nets(circuit):
    on_rf = {
        pin.split(".")[0]
        for net in circuit["nets"] if net["name"] in RF_NETS
        for pin in net["pins"]
    }
    on_rf.discard("U1")
    suffixed = {c["ref"] for c in circuit["components"] if c["ref"].endswith("_rf")}
    assert suffixed == on_rf


@pytest.mark.parametrize("board_file", ["pico-step.kicad_sch", "pico-step.kicad_pcb"])
def test_kicad_refs_match_generator(circuit, board_file):
    gen = {c["ref"] for c in circuit["components"]}
    assert refs_in(ROOT / board_file) == gen
