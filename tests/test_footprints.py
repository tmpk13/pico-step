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
    """Each half bridge is one dual MOSFET: FET1 (S1=1, G1=2, D1=6) high
    side with its drain on VM, FET2 (S2=3, G2=4, D2=5) low side with its
    source on the phase's sense node, bridge center on the motor."""
    nets = {n["name"]: set(n["pins"]) for n in circuit["nets"]}
    bridges = [
        # (dual FET, H pin, L pin, BM pin, C pin, sense net, J4 pin)
        ("Q1", "41", "39", "40", "42", "TMC_SA", "1"),
        ("Q2", "36", "38", "37", "35", "TMC_SA", "2"),
        ("Q3", "1", "47", "48", "2", "TMC_SB", "3"),
        ("Q4", "44", "46", "45", "43", "TMC_SB", "4"),
    ]

    def net_of(pin):
        hits = [name for name, pins in nets.items() if pin in pins]
        assert len(hits) == 1, (pin, hits)
        return hits[0]

    for q, h, low, bm, c, sense, j in bridges:
        assert net_of(f"{q}.2") == net_of(f"U5.{h}")
        assert net_of(f"{q}.4") == net_of(f"U5.{low}")
        assert net_of(f"{q}.6") == "VM"
        out = net_of(f"U5.{bm}")
        assert {f"{q}.1", f"{q}.5", f"J4.{j}"} <= nets[out]
        assert f"{q}.3" in nets[sense]
        boot = [p for p in nets[net_of(f"U5.{c}")] if p != f"U5.{c}"]
        assert len(boot) == 1 and f"{boot[0].split('.')[0]}.2" in nets[out]


def test_dual_fet_units_split_pins(circuit):
    """Unit 1 of the stock dual symbol carries pins 1, 2, 6 and unit 2 carries
    3, 4, 5; each Q must place both units."""
    units = {}
    for c in circuit["components"]:
        if c["lib_id"] == "Transistor_FET:Q_Dual_NMOS_S1G1S2G2D2D1":
            units.setdefault(c["ref"], set()).add(c.get("unit"))
    assert units == {q: {1, 2} for q in ("Q1", "Q2", "Q3", "Q4")}


def test_powerpak_so8l_dual_matches_datasheet():
    """Vishay doc 63817 minimum pads, shifted so the 4.90 x 4.37 mm body is
    centered (pad pattern origin sits 0.18 mm above the body center)."""
    fp = footprints.vishay_powerpak_so8l_dual()
    by_num: dict[str, list] = {}
    for p in fp.pads:
        by_num.setdefault(p.number, []).append(p)
    assert sorted(by_num) == ["1", "2", "3", "4", "5", "6"]
    leads = [by_num[n][0] for n in "1234"]
    # Pins 1..4 left to right along the lead edge, 1.27 pitch, 0.41 x 0.72.
    assert [p.x for p in leads] == pytest.approx([-1.905, -0.635, 0.635, 1.905])
    assert all((p.w, p.h) == (0.41, 0.72) for p in leads)
    assert all(p.y + p.h / 2 == pytest.approx(3.075 + 0.18) for p in leads)

    def extent(ps):
        return (min(p.x - p.w / 2 for p in ps), max(p.x + p.w / 2 for p in ps),
                min(p.y - p.h / 2 for p in ps), max(p.y + p.h / 2 for p in ps))

    # D1 (pad 6) sits over pins 1-2, D2 (pad 5) over pins 3-4.
    d1, d2 = extent(by_num["6"]), extent(by_num["5"])
    assert d1[1] == pytest.approx(-0.25) and d2[0] == pytest.approx(0.25)
    assert d1[0] == pytest.approx(-2.565) and d2[1] == pytest.approx(2.565)
    assert d1[2] == pytest.approx(-3.075 + 0.18)
    # Overall land pattern 5.13 x 6.15.
    allx = extent(fp.pads)
    assert allx[1] - allx[0] == pytest.approx(5.13)
    assert allx[3] - allx[2] == pytest.approx(6.15)


def test_symbol_library_is_current():
    import symbols

    text = (ROOT / "lib" / "pico-step.kicad_sym").read_text()
    for make in symbols.SYMBOLS:
        assert symbols.render(make()) in text
