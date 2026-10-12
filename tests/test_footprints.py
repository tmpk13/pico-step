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


def test_tmc5160_symbol_has_every_pin_once():
    import symbols

    nums = [p.number for p in symbols.tmc5160().pins()]
    assert sorted(nums, key=int) == [str(n) for n in range(1, 50)]


def test_tmc5160_pin_names_match_data_sheet():
    import symbols

    # TMC5160A data sheet Rev 1.18, Signal Descriptions, TQFP column.
    # 49 is the exposed die pad.
    expected = {
        1: "HB1", 2: "CB1", 3: "12VOUT", 4: "VSA", 5: "5VOUT", 6: "GNDA",
        7: "SRAL", 8: "SRAH", 9: "SRBH", 10: "SRBL", 11: "TST_MODE",
        12: "CLK", 13: "CSN_CFG3", 14: "SCK_CFG2", 15: "SDI_CFG1",
        16: "SDO_CFG0", 17: "REFL_STEP", 18: "REFR_DIR", 19: "GNDD",
        20: "VCC_IO", 21: "SD_MODE", 22: "SPI_MODE", 23: "ENCB_DCEN_CFG4",
        24: "ENCA_DCIN_CFG5", 25: "ENCN_DCO_CFG6", 26: "DIAG0_SWN",
        27: "DIAG1_SWP", 28: "DRV_ENN", 29: "VCC", 30: "GNDD", 31: "CPO",
        32: "CPI", 33: "VS", 34: "VCP", 35: "CA2", 36: "HA2", 37: "BMA2",
        38: "LA2", 39: "LA1", 40: "BMA1", 41: "HA1", 42: "CA1", 43: "CB2",
        44: "HB2", 45: "BMB2", 46: "LB2", 47: "LB1", 48: "BMB1", 49: "EP",
    }
    got = {int(p.number): p.name for p in symbols.tmc5160().pins()}
    assert got == expected


def test_tmc5160_bridges_wired_per_phase(circuit):
    """Each half bridge: gate pins on the right FETs, high side drain on VM,
    low side source on its phase's sense node, bridge center on the motor."""
    nets = {n["name"]: set(n["pins"]) for n in circuit["nets"]}
    bridges = [
        # (high FET, low FET, H pin, L pin, BM pin, C pin, sense net, J4 pin)
        ("Q1", "Q2", "41", "39", "40", "42", "TMC_SA", "1"),
        ("Q3", "Q4", "36", "38", "37", "35", "TMC_SA", "2"),
        ("Q5", "Q6", "1", "47", "48", "2", "TMC_SB", "3"),
        ("Q7", "Q8", "44", "46", "45", "43", "TMC_SB", "4"),
    ]

    def net_of(pin):
        hits = [name for name, pins in nets.items() if pin in pins]
        assert len(hits) == 1, (pin, hits)
        return hits[0]

    for hs, ls, h, low, bm, c, sense, j in bridges:
        assert net_of(f"{hs}.4") == net_of(f"U5.{h}")
        assert net_of(f"{ls}.4") == net_of(f"U5.{low}")
        assert net_of(f"{hs}.5") == "VM"
        out = net_of(f"U5.{bm}")
        assert {f"{hs}.1", f"{hs}.2", f"{hs}.3", f"{ls}.5", f"J4.{j}"} <= nets[out]
        assert {f"{ls}.1", f"{ls}.2", f"{ls}.3"} <= nets[sense]
        boot = [p for p in nets[net_of(f"U5.{c}")] if p != f"U5.{c}"]
        assert len(boot) == 1 and f"{boot[0].split('.')[0]}.2" in nets[out]


def test_symbol_library_is_current():
    import symbols

    text = (ROOT / "lib" / "pico-step.kicad_sym").read_text()
    for make in symbols.SYMBOLS:
        assert symbols.render(make()) in text
