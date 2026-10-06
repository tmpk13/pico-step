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


def test_tmc2240_symbol_has_every_pin_once():
    import symbols

    nums = [p.number for p in symbols.tmc2240().pins()]
    assert sorted(nums, key=int) == [str(n) for n in range(1, 34)]


def test_tmc2240_pin_names_match_data_sheet():
    import symbols

    # TQFN32 pin configuration drawing, TMC2240 data sheet Rev 2.
    expected = {
        1: "IREF", 2: "AIN", 3: "VDD1V8", 4: "AGND", 5: "VCC_IO", 6: "ENCN",
        7: "ENCB", 8: "ENCA", 9: "DRV_ENN", 10: "UART_EN", 11: "DIAG0",
        12: "DIAG1/SW", 13: "OV", 14: "CPI", 15: "CPO", 16: "VCP", 17: "VS",
        18: "OUT1B", 19: "OUT2B", 20: "VS", 21: "VS", 22: "OUT2A", 23: "OUT1A",
        24: "VS", 25: "SLEEPN", 26: "CSN/AD2", 27: "SCK/AD1", 28: "SDI/AD0",
        29: "SDO/NAO", 30: "CLK", 31: "STEP", 32: "DIR", 33: "GND",
    }
    got = {int(p.number): p.name for p in symbols.tmc2240().pins()}
    assert got == expected


def test_symbol_library_is_current():
    import symbols

    text = (ROOT / "lib" / "pico-step.kicad_sym").read_text()
    for make in symbols.SYMBOLS:
        assert symbols.render(make()) in text
