"""Cross-check the circuit description against the footprints it names.

ERC and the kicad-vis netlist proof only look at symbols. A pin number
that has no pad on the footprint (or a pad no pin reaches) passes both and
only shows up as an unconnected pad after "Update PCB from Schematic".
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STOCK = Path("/usr/share/kicad/footprints")
sys.path.insert(0, str(ROOT / "tools"))

import footprints  # noqa: E402


@pytest.fixture(scope="module")
def circuit() -> dict:
    out = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "circuit.py")],
        check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out)


def footprint_file(ref: str) -> Path:
    lib, name = ref.split(":", 1)
    if lib == "pico-step":
        return ROOT / "lib" / "pico-step.pretty" / f"{name}.kicad_mod"
    return STOCK / f"{lib}.pretty" / f"{name}.kicad_mod"


def pad_names(path: Path) -> set[str]:
    return {p for p in re.findall(r'\(pad "([^"]*)"', path.read_text()) if p}


def used_pins(circuit: dict) -> dict[str, set[str]]:
    used: dict[str, set[str]] = {}
    endpoints = [p for n in circuit["nets"] for p in n["pins"]] + circuit["no_connect"]
    for ep in endpoints:
        ref, pin = ep.split(".", 1)
        used.setdefault(ref, set()).add(pin)
    return used


def test_footprints_exist(circuit):
    for c in circuit["components"]:
        assert footprint_file(c["footprint"]).is_file(), c["footprint"]


def test_every_pin_has_a_pad(circuit):
    used = used_pins(circuit)
    for c in circuit["components"]:
        pads = pad_names(footprint_file(c["footprint"]))
        missing = used.get(c["ref"], set()) - pads
        assert not missing, f"{c['ref']} pins {missing} not on {c['footprint']}"


def test_every_pad_is_used(circuit):
    used = used_pins(circuit)
    for c in circuit["components"]:
        pads = pad_names(footprint_file(c["footprint"]))
        orphan = pads - used.get(c["ref"], set())
        assert not orphan, f"{c['ref']} pads {orphan} on no net and not no_connect"


def test_pg_dso_8_matches_datasheet():
    fp = footprints.pg_dso_8()
    xs = sorted({p.x for p in fp.pads})
    ys = sorted({p.y for p in fp.pads})
    assert xs == pytest.approx([-2.845, 2.845])
    assert [round(b - a, 4) for a, b in zip(ys, ys[1:])] == [1.27] * 3
    assert all((p.w, p.h) == (1.31, 0.65) for p in fp.pads)
    # Pin 1 top left, pin 8 top right.
    by_num = {p.number: p for p in fp.pads}
    assert by_num["1"].x < 0 and by_num["1"].y < 0
    assert by_num["8"].x > 0 and by_num["8"].y == by_num["1"].y


def test_generated_library_is_current():
    for make in footprints.FOOTPRINTS:
        fp = make()
        path = ROOT / "lib" / "pico-step.pretty" / f"{fp.name}.kicad_mod"
        assert path.read_text() == fp.render(), f"rerun tools/footprints.py for {fp.name}"
