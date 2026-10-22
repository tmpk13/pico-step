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


@dataclass
class Symbol:
    name: str
    reference: str
    footprint: str
    datasheet: str
    description: str
    keywords: str
    left: list[Pin | None]
    right: list[Pin | None]
    top: list[Pin | None]
    bottom: list[Pin | None]
    mpn: str = ""
    manufacturer: str = ""

    def pins(self) -> list[Pin]:
        return [p for side in (self.left, self.right, self.top, self.bottom) for p in side if p]


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
    half_w = max(cols + 1, 8) * G / 2
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
    for i, p in enumerate(s.left):
        if p:
            pins.append(pin_sexpr(p, -half_w - PIN_LEN, y0 - i * G, 0))
    for i, p in enumerate(s.right):
        if p:
            pins.append(pin_sexpr(p, half_w + PIN_LEN, y0 - i * G, 180))
    x0 = -(len(s.top) - 1) * G / 2
    for i, p in enumerate(s.top):
        if p:
            pins.append(pin_sexpr(p, x0 + i * G, half_h + PIN_LEN, 270))
    x0 = -(len(s.bottom) - 1) * G / 2
    for i, p in enumerate(s.bottom):
        if p:
            pins.append(pin_sexpr(p, x0 + i * G, -half_h - PIN_LEN, 90))

    if s.top or s.bottom:
        # Top and bottom pin numbers occupy the edges above and below the
        # body, so the texts sit outside its top left and bottom right corners.
        ref = prop("Reference", s.reference, -half_w - 1.27, half_h + 1.27, False, "right bottom")
        val = prop("Value", s.name, half_w + 1.27, -half_h - 1.27, False, "left top")
    else:
        ref = prop("Reference", s.reference, -half_w, half_h + 1.27, False, "left bottom")
        val = prop("Value", s.name, half_w, half_h + 1.27, False, "right bottom")
    out = [
        f'\t(symbol "{s.name}"\n',
        "\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)\n",
        ref,
        val,
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


def tmc5241() -> Symbol:
    # TMC5241 data sheet Rev. 0, Pin Descriptions and the TQFN pin
    # configuration (top view: pins 1..12 along one 7 mm side, then counter
    # clockwise). Slashes in the data sheet names are underscores here. The
    # N.C. pins are passive so they stay in the netlist; the data sheet
    # allows tying them to GND for cooling. The exposed pad is GND and pin
    # 39 to match the footprint.
    P = Pin
    return Symbol(
        name="TMC5241",
        reference="U",
        footprint="pico-step:ADI_TQFN-38-1EP_5x7mm_P0.5mm_EP3.65x5.6mm_ThermalVias",
        datasheet="https://www.analog.com/media/en/technical-documentation/data-sheets/tmc5241.pdf",
        description="65V 2A RMS stepper driver with motion controller, integrated MOSFETs and current sensing, SPI/UART, TQFN-38-EP 5x7mm",
        keywords="stepper driver controller Trinamic ADI SPI StealthChop integrated",
        mpn="TMC5241ATU+T",
        manufacturer="Analog Devices",
        # Blank rows keep the side pin names clear of the vertical top and
        # bottom pin names.
        left=[
            None, None, None,
            P("34", "CSN_AD2", "input"),
            P("35", "SCK_AD1", "input"),
            P("36", "SDI_AD0", "input"),
            P("37", "SDO_NAO", "tri_state"),
            None,
            P("1", "REFL", "input"),
            P("2", "REFR", "input"),
            P("11", "DRV_ENN", "input"),
            P("33", "nSLEEP", "input"),
            None,
            P("13", "DIAG0", "output"),
            P("14", "DIAG1_SW", "bidirectional"),
            P("15", "OV", "open_collector"),
            None,
            P("10", "ENCA", "input"),
            P("9", "ENCB", "input"),
            P("8", "ENCN", "input"),
            None,
            P("12", "UART_EN", "input"),
            P("38", "CLK", "input"),
            None, None,
        ],
        right=[
            None, None, None,
            P("29", "OUT1A", "output"),
            P("27", "OUT2A", "output"),
            None,
            P("22", "OUT1B", "output"),
            P("24", "OUT2B", "output"),
            None,
            P("18", "VCP", "passive"),
            P("16", "CPI", "passive"),
            P("17", "CPO", "passive"),
            None,
            P("3", "IREF", "passive"),
            P("4", "AIN", "input"),
            None, None,
        ],
        top=[
            P("30", "VS", "power_in"),
            P("26", "VS", "power_in"),
            P("25", "VS", "power_in"),
            P("21", "VS", "power_in"),
            None,
            P("5", "VDD1V8", "power_out"),
            P("7", "VCC_IO", "power_in"),
        ],
        bottom=[
            P("6", "AGND", "power_in"),
            P("23", "PGND", "power_in"),
            P("28", "PGND", "power_in"),
            P("39", "EP", "power_in"),
            None,
            P("19", "NC", "passive"),
            P("20", "NC", "passive"),
            P("31", "NC", "passive"),
            P("32", "NC", "passive"),
        ],
    )


SYMBOLS = [tmc5241]


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
