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


SYMBOLS = [tmc2240]


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
