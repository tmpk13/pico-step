"""Cross-check the schematic against the footprints it names.

ERC and tsch's netlist proof only look at symbols. A pin number that has
no pad on the footprint (or a pad no pin reaches) passes both and only
shows up as an unconnected pad after updating the board.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STOCK = Path("/usr/share/kicad/footprints")
sys.path.insert(0, str(ROOT / "tools"))

import footprints  # noqa: E402


def footprint_file(ref: str) -> Path:
    lib, name = ref.split(":", 1)
    if lib == "pico-step":
        return ROOT / "lib" / "pico-step.pretty" / f"{name}.kicad_mod"
    return STOCK / f"{lib}.pretty" / f"{name}.kicad_mod"


def pad_names(path: Path) -> set[str]:
    return {p for p in re.findall(r'\(pad "([^"]*)"', path.read_text()) if p}


def used_pins(schematic: dict) -> dict[str, set[str]]:
    used: dict[str, set[str]] = {}
    endpoints = [p for n in schematic["nets"] for p in n["pins"]] + schematic["no_connect"]
    for ep in endpoints:
        ref, pin = ep.split(".", 1)
        used.setdefault(ref, set()).add(pin)
    return used


def test_footprints_exist(schematic):
    for c in schematic["components"]:
        assert footprint_file(c["footprint"]).is_file(), c["footprint"]


def test_every_pin_has_a_pad(schematic):
    used = used_pins(schematic)
    for c in schematic["components"]:
        pads = pad_names(footprint_file(c["footprint"]))
        missing = used.get(c["ref"], set()) - pads
        assert not missing, f"{c['ref']} pins {missing} not on {c['footprint']}"


def test_every_pad_is_used(schematic):
    used = used_pins(schematic)
    for c in schematic["components"]:
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


def u5_pin_names(schematic: dict) -> dict[int, str]:
    return {int(p.split(".")[1]): name for p, name in schematic["pin_names"].items()
            if p.startswith("U5.")}


def test_tmc5241_symbol_has_every_pin_once(schematic):
    assert sorted(u5_pin_names(schematic)) == list(range(1, 40))


def test_tmc5241_pin_names_match_data_sheet(schematic):
    # TMC5241 data sheet Rev. 0, Pin Descriptions and TQFN pin
    # configuration, "/" written as "_". 39 is the exposed pad (GND).
    expected = {
        1: "REFL", 2: "REFR", 3: "IREF", 4: "AIN", 5: "VDD1V8", 6: "AGND",
        7: "VCC_IO", 8: "ENCN", 9: "ENCB", 10: "ENCA", 11: "DRV_ENN",
        12: "UART_EN", 13: "DIAG0", 14: "DIAG1_SW", 15: "OV", 16: "CPI",
        17: "CPO", 18: "VCP", 19: "NC", 20: "NC", 21: "VS", 22: "OUT1B",
        23: "PGND", 24: "OUT2B", 25: "VS", 26: "VS", 27: "OUT2A",
        28: "PGND", 29: "OUT1A", 30: "VS", 31: "NC", 32: "NC",
        33: "nSLEEP", 34: "CSN_AD2", 35: "SCK_AD1", 36: "SDI_AD0",
        37: "SDO_NAO", 38: "CLK", 39: "EP",
    }
    assert u5_pin_names(schematic) == expected


def test_tmc5241_support_circuit(schematic):
    """Supply, strap and output pins per the data sheet's Figure 50 and pin
    table: VS on the motor supply, VCC_IO on 3V3, VDD1V8 and IREF each to one
    part going to GND, SPI and internal clock straps low, OV unused."""
    nets = {n["name"]: set(n["pins"]) for n in schematic["nets"]}

    def net_of(pin):
        hits = [name for name, pins in nets.items() if pin in pins]
        assert len(hits) == 1, (pin, hits)
        return hits[0]

    assert {net_of(f"U5.{p}") for p in (21, 25, 26, 30)} == {"VM"}
    assert net_of("U5.7") == "+3V3"
    # AGND, PGND, EP, UART_EN, CLK, AIN and the four N.C. pins.
    for p in (6, 23, 28, 39, 12, 38, 4, 19, 20, 31, 32):
        assert net_of(f"U5.{p}") == "GND", p
    assert "U5.15" in schematic["no_connect"]
    for pin in ("U5.5", "U5.3"):
        others = nets[net_of(pin)] - {pin}
        assert len(others) == 1
        ref, n = others.pop().split(".")
        assert net_of(f"{ref}.{3 - int(n)}") == "GND"
    # Charge pump: VCP to VS through one capacitor, CPI to CPO through one.
    vcp = nets[net_of("U5.18")] - {"U5.18"}
    assert len(vcp) == 1 and net_of(vcp.pop().replace(".2", ".1")) == "VM"
    cpi, cpo = nets[net_of("U5.16")] - {"U5.16"}, nets[net_of("U5.17")] - {"U5.17"}
    assert len(cpi) == len(cpo) == 1 and cpi.pop()[:-2] == cpo.pop()[:-2]
    # Motor connector order 1A 2A 1B 2B.
    for p, j in ((29, 1), (27, 2), (22, 3), (24, 4)):
        assert f"J4.{j}" in nets[net_of(f"U5.{p}")]


def test_tqfn38_matches_land_pattern():
    """ADI/Maxim land pattern 90-0076 rev C, turned with the 12-pad rows
    vertical and pin 1 at the top of the left row."""
    fp = footprints.adi_tqfn38_5x7()
    sig = {p.number: p for p in fp.pads if p.number and p.number != "39"}
    assert sorted(sig, key=int) == [str(n) for n in range(1, 39)]
    left = [sig[str(n)] for n in range(1, 13)]
    bottom = [sig[str(n)] for n in range(13, 20)]
    right = [sig[str(n)] for n in range(20, 32)]
    top = [sig[str(n)] for n in range(32, 39)]
    assert all((p.w, p.h) == (0.75, 0.25) for p in left + right)
    assert all((p.w, p.h) == (0.25, 0.75) for p in top + bottom)
    # 4.88 between the 12-pad row centers, 6.85 between the 7-pad rows.
    assert right[0].x - left[0].x == pytest.approx(4.88)
    assert bottom[0].y - top[0].y == pytest.approx(6.85)
    # 0.5 mm pitch, counter clockwise from the top left.
    assert [p.y for p in left] == pytest.approx([-2.75 + 0.5 * i for i in range(12)])
    assert [p.x for p in bottom] == pytest.approx([-1.5 + 0.5 * i for i in range(7)])
    assert [p.y for p in right] == pytest.approx([2.75 - 0.5 * i for i in range(12)])
    assert [p.x for p in top] == pytest.approx([1.5 - 0.5 * i for i in range(7)])
    assert left[0].y < 0 and left[0].x < 0
    ep = [p for p in fp.pads if p.number == "39" and not p.drill]
    assert {(p.w, p.h) for p in ep} == {(3.65, 5.60)}
    assert {lay for p in ep for lay in p.layers} == {"F.Cu", "F.Mask", "B.Cu"}
    vias = [p for p in fp.pads if p.drill]
    assert all(p.drill == 0.3 and abs(p.x) + 0.3 < 3.65 / 2 and abs(p.y) + 0.3 < 5.60 / 2
               for p in vias)

