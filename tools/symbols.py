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


def tmc5160() -> Symbol:
    # TMC5160/TMC5160A data sheet Rev 1.18, section 2.2 Signal Descriptions
    # (TQFP column) and Figure 2.1 (TQFP-48 pinning). The exposed die pad is
    # GNDD/GNDP and the low side gate driver ground; it is pin 49 here to
    # match the stock TQFP-48-1EP footprint.
    P = Pin
    return Symbol(
        name="TMC5160A-TA",
        reference="U",
        footprint="Package_QFP:TQFP-48-1EP_7x7mm_P0.5mm_EP5x5mm_ThermalVias",
        datasheet="https://www.analog.com/media/en/technical-documentation/data-sheets/TMC5160A_datasheet_rev1.18.pdf",
        description="60V stepper motion controller and gate driver for external N-MOSFET bridges, SPI/UART + STEP/DIR, TQFP-48-EP 7x7mm",
        keywords="stepper driver controller gate driver Trinamic ADI SPI StealthChop",
        mpn="TMC5160A-TA",
        manufacturer="Analog Devices",
        # Blank rows keep the side pin names clear of the vertical top and
        # bottom pin names.
        left=[
            None, None, None,
            P("13", "CSN_CFG3", "input"),
            P("14", "SCK_CFG2", "input"),
            P("15", "SDI_CFG1", "input"),
            P("16", "SDO_CFG0", "bidirectional"),
            None,
            P("17", "REFL_STEP", "input"),
            P("18", "REFR_DIR", "input"),
            P("28", "DRV_ENN", "input"),
            None,
            P("21", "SD_MODE", "input"),
            P("22", "SPI_MODE", "input"),
            None,
            P("26", "DIAG0_SWN", "bidirectional"),
            P("27", "DIAG1_SWP", "bidirectional"),
            None,
            P("24", "ENCA_DCIN_CFG5", "input"),
            P("23", "ENCB_DCEN_CFG4", "input"),
            P("25", "ENCN_DCO_CFG6", "bidirectional"),
            None,
            P("12", "CLK", "input"),
            P("11", "TST_MODE", "input"),
            None, None,
        ],
        right=[
            None, None, None,
            P("42", "CA1", "passive"),
            P("41", "HA1", "output"),
            P("40", "BMA1", "passive"),
            P("39", "LA1", "output"),
            P("35", "CA2", "passive"),
            P("36", "HA2", "output"),
            P("37", "BMA2", "passive"),
            P("38", "LA2", "output"),
            P("8", "SRAH", "input"),
            P("7", "SRAL", "input"),
            None,
            P("2", "CB1", "passive"),
            P("1", "HB1", "output"),
            P("48", "BMB1", "passive"),
            P("47", "LB1", "output"),
            P("43", "CB2", "passive"),
            P("44", "HB2", "output"),
            P("45", "BMB2", "passive"),
            P("46", "LB2", "output"),
            P("9", "SRBH", "input"),
            P("10", "SRBL", "input"),
            None, None,
        ],
        top=[
            P("33", "VS", "power_in"),
            P("4", "VSA", "power_in"),
            P("34", "VCP", "passive"),
            P("32", "CPI", "passive"),
            P("31", "CPO", "passive"),
            P("3", "12VOUT", "power_out"),
            P("5", "5VOUT", "power_out"),
            P("29", "VCC", "power_in"),
            P("20", "VCC_IO", "power_in"),
        ],
        bottom=[
            P("6", "GNDA", "power_in"),
            P("19", "GNDD", "power_in"),
            None,
            P("30", "GNDD", "power_in"),
            P("49", "EP", "power_in"),
        ],
    )


SYMBOLS = [tmc5160]


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
