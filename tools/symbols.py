#!/usr/bin/env python3
"""Generate project symbols into lib/pico-step.kicad_sym.

Pin numbers and names are transcribed from the manufacturer data sheet's
pin table and checked against its pin configuration drawing.
Run from the project root: python3 tools/symbols.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "lib" / "pico-step.kicad_sym"
G = 2.54
PIN_LEN = 2.54


@dataclass
class Pin:
    number: str
    name: str
    etype: str
    hidden: bool = False


Slot = Pin | list[Pin] | None


def stack(slot: Slot) -> list[Pin]:
    if slot is None:
        return []
    return slot if isinstance(slot, list) else [slot]


@dataclass
class Symbol:
    name: str
    reference: str
    footprint: str
    datasheet: str
    description: str
    keywords: str
    # A slot holds one pin, nothing, or a list of pins stacked on one spot.
    left: list[Slot]
    right: list[Slot]
    top: list[Slot]
    bottom: list[Slot]
    mpn: str = ""
    manufacturer: str = ""
    # Minimum body width in grid units, for long pin names on both sides.
    min_cols: int = 8

    def pins(self) -> list[Pin]:
        return [p for side in (self.left, self.right, self.top, self.bottom)
                for slot in side for p in stack(slot)]


def spaced(pins: list[Pin]) -> list[Slot]:
    """Pins with one empty grid step between neighbors."""
    out: list[Slot] = []
    for p in pins:
        if out:
            out.append(None)
        out.append(p)
    return out


def num(v: float) -> str:
    s = f"{round(v, 4):.4f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def prop(key: str, value: str, x: float, y: float, hide: bool, justify: str = "") -> str:
    eff = "(font (size 1.27 1.27))"
    if justify:
        eff += f" (justify {justify})"
    if hide:
        eff += " (hide yes)"
    return f'\t\t(property "{key}" "{value}" (at {num(x)} {num(y)} 0) (effects {eff}))\n'


def pin_sexpr(p: Pin, x: float, y: float, angle: int) -> str:
    hide = " (hide yes)" if p.hidden else ""
    return (
        f"\t\t\t(pin {p.etype} line (at {num(x)} {num(y)} {angle}) (length {num(PIN_LEN)}){hide}\n"
        f'\t\t\t\t(name "{p.name}" (effects (font (size 1.27 1.27))))\n'
        f'\t\t\t\t(number "{p.number}" (effects (font (size 1.27 1.27)))))\n'
    )


def render(s: Symbol) -> str:
    rows = max(len(s.left), len(s.right))
    cols = max(len(s.top), len(s.bottom))
    half_w = max(cols + 1, s.min_cols) * G / 2
    half_w = round(half_w / G) * G
    half_h = (rows + 1) * G / 2
    half_h = round(half_h / G + 0.49) * G

    body = (
        f"\t\t(symbol \"{s.name}_0_1\"\n"
        f"\t\t\t(rectangle (start {num(-half_w)} {num(half_h)}) (end {num(half_w)} {num(-half_h)})\n"
        "\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background))))\n"
    )

    pins = []
    y0 = half_h - G
    for i, slot in enumerate(s.left):
        for p in stack(slot):
            pins.append(pin_sexpr(p, -half_w - PIN_LEN, y0 - i * G, 0))
    for i, slot in enumerate(s.right):
        for p in stack(slot):
            pins.append(pin_sexpr(p, half_w + PIN_LEN, y0 - i * G, 180))
    x0 = -(len(s.top) - 1) * G / 2
    for i, slot in enumerate(s.top):
        for p in stack(slot):
            pins.append(pin_sexpr(p, x0 + i * G, half_h + PIN_LEN, 270))
    x0 = -(len(s.bottom) - 1) * G / 2
    for i, slot in enumerate(s.bottom):
        for p in stack(slot):
            pins.append(pin_sexpr(p, x0 + i * G, -half_h - PIN_LEN, 90))

    out = [
        f'\t(symbol "{s.name}"\n',
        "\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)\n",
        prop("Reference", s.reference, -half_w, half_h + 1.27, False, "left bottom"),
        prop("Value", s.name, half_w, half_h + 1.27, False, "right bottom"),
        prop("Footprint", s.footprint, 0, -half_h - 5.08, True),
        prop("Datasheet", s.datasheet, 0, -half_h - 7.62, True),
        prop("Description", s.description, 0, -half_h - 10.16, True),
        prop("ki_keywords", s.keywords, 0, 0, True),
    ]
    if s.mpn:
        out.append(prop("MPN", s.mpn, 0, -half_h - 12.7, True))
    if s.manufacturer:
        out.append(prop("Manufacturer", s.manufacturer, 0, -half_h - 15.24, True))
    out.append(body)
    out.append(f'\t\t(symbol "{s.name}_1_1"\n')
    out.extend(pins)
    out.append("\t\t)\n\t)\n")
    return "".join(out)


def tmc2240() -> Symbol:
    # TMC2240 data sheet Rev 2 (19-101548), Pin Description, TQFN32 column,
    # and "TMC2240 TQFN Pin Configuration". The TQFN has no PGND pins (those
    # are TSSOP38 only); ground is AGND plus the exposed pad.
    P = Pin
    return Symbol(
        name="TMC2240",
        reference="U",
        footprint="pico-step:Maxim_TQFN-32-1EP_5x5mm_P0.5mm_T3255-5",
        datasheet="https://www.analog.com/media/en/technical-documentation/data-sheets/tmc2240_datasheet.pdf",
        description="36V 2A RMS stepper driver, STEP/DIR + SPI/UART, integrated current sensing, TQFN-32 5x5mm",
        keywords="stepper driver Trinamic ADI SPI StealthChop",
        mpn="TMC2240ATJ+T",
        manufacturer="Analog Devices",
        left=[
            P("26", "CSN/AD2", "input"),
            P("27", "SCK/AD1", "input"),
            P("28", "SDI/AD0", "input"),
            P("29", "SDO/NAO", "tri_state"),
            None,
            P("31", "STEP", "input"),
            P("32", "DIR", "input"),
            P("9", "DRV_ENN", "input"),
            P("25", "SLEEPN", "input"),
            None,
            P("11", "DIAG0", "output"),
            P("12", "DIAG1/SW", "bidirectional"),
            P("13", "OV", "open_collector"),
            None,
            P("8", "ENCA", "input"),
            P("7", "ENCB", "input"),
            P("6", "ENCN", "input"),
            None,
            P("10", "UART_EN", "input"),
            P("30", "CLK", "input"),
        ],
        right=[
            P("17", "VS", "power_in"),
            P("20", "VS", "power_in"),
            P("21", "VS", "power_in"),
            P("24", "VS", "power_in"),
            P("5", "VCC_IO", "power_in"),
            None,
            P("23", "OUT1A", "output"),
            P("22", "OUT2A", "output"),
            P("18", "OUT1B", "output"),
            P("19", "OUT2B", "output"),
            None,
            P("16", "VCP", "passive"),
            P("14", "CPI", "passive"),
            P("15", "CPO", "passive"),
            None,
            P("3", "VDD1V8", "power_out"),
            P("1", "IREF", "passive"),
            P("2", "AIN", "input"),
            None,
            P("4", "AGND", "power_in"),
            P("33", "GND", "power_in"),
        ],
        top=[],
        bottom=[],
    )


def esp32_c5hf4() -> Symbol:
    # ESP32-C5 Series Datasheet v1.5, Figure 2-2 "ESP32-C5HF4 Pin Layout",
    # Table 2-1 "Pin Overview" and Table 2-3 "IO MUX Pin Functions" (GPIO
    # numbers). On the HF4 the in-package flash occupies the SPI pins, so
    # pins 26..32 are NC; pin 25 (SPICS1, GPIO15) stays an IO.
    P = Pin

    def io(number: str, name: str) -> Pin:
        return P(number, name, "bidirectional")

    def vdd(number: str, name: str) -> Pin:
        return P(number, name, "power_in")

    return Symbol(
        name="ESP32-C5HF4",
        reference="U",
        footprint="Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.66x4.66mm_ThermalVias",
        datasheet="https://www.espressif.com/sites/default/files/documentation/esp32-c5_datasheet_en.pdf",
        description="RISC-V SoC, dual-band 2.4/5 GHz Wi-Fi 6, Bluetooth LE 5, 802.15.4, 4 MB in-package flash, QFN-48 6x6mm",
        keywords="ESP32 Espressif WiFi 5GHz BLE Zigbee Thread RISC-V",
        mpn="ESP32-C5HF4",
        manufacturer="Espressif Systems",
        # Side pins start three rows down, below the names of the top pins.
        left=[
            None, None, None,
            P("7", "CHIP_PU", "input"),
            None,
            P("5", "XTAL_P", "passive"),
            P("4", "XTAL_N", "passive"),
            None,
            P("42", "ANT_2G", "passive"),
            P("48", "ANT_5G", "passive"),
            None,
            *spaced([P(n, "GND", "power_in") for n in ("2", "43", "47", "49")]),
        ],
        right=[
            None, None, None,
            io("9", "GPIO0/XTAL_32K_P"),
            io("10", "GPIO1/XTAL_32K_N"),
            io("11", "GPIO2/MTMS"),
            io("12", "GPIO3/MTDI"),
            io("13", "GPIO4/MTCK"),
            io("14", "GPIO5/MTDO"),
            io("15", "GPIO6"),
            io("16", "GPIO7"),
            io("17", "GPIO8"),
            io("18", "GPIO9"),
            io("19", "GPIO10"),
            io("20", "GPIO11/U0TXD"),
            io("21", "GPIO12/U0RXD"),
            io("22", "GPIO13/USB_D-"),
            io("23", "GPIO14/USB_D+"),
            io("25", "GPIO15/SPICS1"),
            None,
            io("33", "GPIO23"),
            io("34", "GPIO24"),
            io("35", "GPIO25"),
            io("36", "GPIO26"),
            io("37", "GPIO27"),
            io("38", "GPIO28"),
            None,
            *(P(str(n), "NC", "passive") for n in range(26, 33)),
        ],
        # One empty grid step between supply pins leaves room for a rail
        # symbol's name above each one; the wider gap in the middle keeps
        # the reference designator clear.
        top=spaced([
            vdd("1", "VDDA6"), vdd("3", "VDDA7"), vdd("6", "VDDA8"),
            vdd("8", "VDDPST1"), vdd("24", "VDDPST2"), vdd("39", "VDDPST3"),
        ]) + [None] * 5 + spaced([
            vdd("40", "VDDA1"), vdd("41", "VDDA2"), vdd("44", "VDDA3"),
            vdd("45", "VDDA4"), vdd("46", "VDDA5"),
        ]),
        bottom=[],
    )


def lfd182g45dchd481() -> Symbol:
    # Murata LFD182G45DCHD481 specification No.CD481-01, Terminal
    # Configuration. Terminals 4 and 8 are NC and must not touch any copper,
    # so the symbol and land pattern omit them.
    P = Pin
    return Symbol(
        name="LFD182G45DCHD481",
        reference="FL",
        footprint="pico-step:Murata_LFD182G45DCHD481",
        datasheet="https://pim.murata.com/asset/pim4/lcDiplexer/LFD182G45DCHD481_PDF_LCDIPLEXER",
        description="Dual-band diplexer, 2450 MHz / 5425 MHz, 1.6x0.8mm",
        keywords="diplexer RF 2.4GHz 5GHz WiFi Murata",
        mpn="LFD182G45DCHD481",
        manufacturer="Murata Electronics",
        left=[
            P("3", "P2_LF", "passive"),
            None,
            P("1", "P1_HF", "passive"),
        ],
        right=[
            None,
            P("6", "P3_COM", "passive"),
            None,
            *spaced([P(n, "GND", "passive") for n in ("2", "5", "7")]),
        ],
        top=[],
        bottom=[],
    )


SYMBOLS = [tmc2240, esp32_c5hf4, lfd182g45dchd481]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(render(make()) for make in SYMBOLS)
    OUT.write_text(
        "(kicad_symbol_lib\n\t(version 20241209)\n\t(generator \"pico-step-symbols\")\n"
        "\t(generator_version \"10.0\")\n" + body + ")\n"
    )
    print(f"wrote {OUT.relative_to(OUT.parent.parent)}")


if __name__ == "__main__":
    main()
