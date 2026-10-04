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


def test_esp32_c5hf4_symbol_has_every_pin_once():
    import symbols

    nums = [p.number for p in symbols.esp32_c5hf4().pins()]
    assert sorted(nums, key=int) == [str(n) for n in range(1, 50)]


def test_esp32_c5hf4_pin_names_match_data_sheet():
    import symbols

    # ESP32-C5 Series Datasheet v1.5, Figure 2-2 (HF4 pin layout); GPIO
    # numbers from Table 2-3. The symbol prefixes the GPIO number where the
    # drawing shows a function name.
    expected = {
        1: "VDDA6", 2: "GND", 3: "VDDA7", 4: "XTAL_N", 5: "XTAL_P", 6: "VDDA8",
        7: "CHIP_PU", 8: "VDDPST1", 9: "GPIO0/XTAL_32K_P", 10: "GPIO1/XTAL_32K_N",
        11: "GPIO2/MTMS", 12: "GPIO3/MTDI", 13: "GPIO4/MTCK", 14: "GPIO5/MTDO",
        15: "GPIO6", 16: "GPIO7", 17: "GPIO8", 18: "GPIO9", 19: "GPIO10",
        20: "GPIO11/U0TXD", 21: "GPIO12/U0RXD", 22: "GPIO13/USB_D-",
        23: "GPIO14/USB_D+", 24: "VDDPST2", 25: "GPIO15/SPICS1",
        **{n: "NC" for n in range(26, 33)},
        33: "GPIO23", 34: "GPIO24", 35: "GPIO25", 36: "GPIO26", 37: "GPIO27",
        38: "GPIO28", 39: "VDDPST3", 40: "VDDA1", 41: "VDDA2", 42: "ANT_2G",
        43: "GND", 44: "VDDA3", 45: "VDDA4", 46: "VDDA5", 47: "GND",
        48: "ANT_5G", 49: "GND",
    }
    got = {int(p.number): p.name for p in symbols.esp32_c5hf4().pins()}
    assert got == expected


def test_diplexer_symbol_matches_murata_terminals():
    import symbols

    # Murata spec CD481-01 Terminal Configuration; 4 and 8 are NC with no land.
    expected = {1: "P1_HF", 2: "GND", 3: "P2_LF", 5: "GND", 6: "P3_COM", 7: "GND"}
    got = {int(p.number): p.name for p in symbols.lfd182g45dchd481().pins()}
    assert got == expected


def test_diplexer_land_pattern_matches_murata():
    fp = footprints.murata_lfd18()
    by_num = {p.number: p for p in fp.pads}
    assert sorted(by_num) == ["1", "2", "3", "5", "6", "7"]
    # 0.25 x 0.5 mm lands (turned 90 degrees), 0.5 mm pitch, land rows
    # 0.2..0.7 mm either side of the center line.
    assert all((p.w, p.h) == (0.5, 0.25) for p in fp.pads)
    assert all(abs(p.x) - p.w / 2 == pytest.approx(0.2) for p in fp.pads)
    assert all(abs(p.x) + p.w / 2 == pytest.approx(0.7) for p in fp.pads)
    left = [by_num[n].y for n in ("1", "2", "3")]
    right = [by_num[n].y for n in ("7", "6", "5")]
    assert left == right == pytest.approx([-0.5, 0.0, 0.5])
    # Terminal 1 top left, the signal ports diagonally apart from P3.
    assert by_num["1"].x < 0 and by_num["6"].x > 0


def net_of(circuit: dict, pin: str) -> tuple[str, set[str]]:
    for n in circuit["nets"]:
        if pin in n["pins"]:
            return n["name"], set(n["pins"])
    raise AssertionError(f"{pin} on no net")


def test_esp32_boot_straps(circuit):
    # Data sheet Table 3-3: GPIO28 low at reset selects download mode, and
    # USB download (Joint Download Boot 0) also needs GPIO27 high.
    _, boot = net_of(circuit, "U1.38")
    assert {"SW1.1", "R6.2"} <= boot
    _, pullup = net_of(circuit, "R6.1")
    assert "U2.5" in pullup  # +3V3
    # GPIO27 shares a net only with DRV_ENN, which has an internal pull-up.
    # TMC2240 DIAG0 is driven low in reset and must not land here.
    _, gpio27 = net_of(circuit, "U1.37")
    assert gpio27 == {"U1.37", "U5.9"}


def test_esp32_vm_sense_on_adc1(circuit):
    # Table 2-7: ADC1_CH0..CH5 are GPIO1..GPIO6, pins 10..15.
    name, pins = net_of(circuit, "R13.1")
    assert name == "VM_SENSE"
    mcu = {int(p.split(".")[1]) for p in pins if p.startswith("U1.")}
    assert mcu and mcu <= set(range(10, 16))


def test_esp32_usb_pins(circuit):
    assert net_of(circuit, "U1.23")[0] == "USB_DP"  # GPIO14, USB_D+
    assert net_of(circuit, "U1.22")[0] == "USB_DM"  # GPIO13, USB_D-


def test_esp32_hf4_nc_pins_unconnected(circuit):
    on_nets = {p for n in circuit["nets"] for p in n["pins"]}
    for n in range(26, 33):
        assert f"U1.{n}" in circuit["no_connect"]
        assert f"U1.{n}" not in on_nets
