#!/usr/bin/env python3
"""Generate project footprints into lib/pico-step.pretty.

Each footprint is described by its land pattern as given in the
manufacturer data sheet, so dimensions stay traceable to one figure.
Run from the project root: python3 tools/footprints.py
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "lib" / "pico-step.pretty"
NAMESPACE = uuid.UUID("6f1c3a52-6a1e-4b8e-9d55-2f6a1c0b7e01")

SILK_W = 0.12
FAB_W = 0.10
CRT_W = 0.05
CRT_MARGIN = 0.25


def grid(v: float, step: float = 0.01) -> float:
    return round(round(v / step) * step, 4)


def num(v: float) -> str:
    s = f"{grid(v, 0.0001):.4f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


@dataclass
class Pad:
    number: str
    x: float
    y: float
    w: float
    h: float
    shape: str = "roundrect"


@dataclass
class Footprint:
    name: str
    descr: str
    tags: str
    body_w: float
    body_h: float
    pads: list[Pad]
    model: str | None = None
    fab_marks: list[tuple[float, float]] = field(default_factory=list)

    def _uid(self, *parts: object) -> str:
        return str(uuid.uuid5(NAMESPACE, "/".join([self.name, *map(str, parts)])))

    def _line(self, x1, y1, x2, y2, layer, width) -> str:
        return (
            f'\t(fp_line (start {num(x1)} {num(y1)}) (end {num(x2)} {num(y2)})\n'
            f'\t\t(stroke (width {num(width)}) (type solid)) (layer "{layer}")\n'
            f'\t\t(uuid "{self._uid("line", layer, x1, y1, x2, y2)}"))\n'
        )

    def _rect(self, x1, y1, x2, y2, layer, width) -> str:
        return (
            self._line(x1, y1, x2, y1, layer, width)
            + self._line(x2, y1, x2, y2, layer, width)
            + self._line(x2, y2, x1, y2, layer, width)
            + self._line(x1, y2, x1, y1, layer, width)
        )

    def _text(self, kind: str, value: str, y: float, layer: str) -> str:
        return (
            f'\t(property "{kind}" "{value}" (at 0 {num(y)} 0) (layer "{layer}")\n'
            f'\t\t(uuid "{self._uid("prop", kind)}")\n'
            "\t\t(effects (font (size 1 1) (thickness 0.15))))\n"
        )

    def render(self) -> str:
        pad_x0 = min(p.x - p.w / 2 for p in self.pads)
        pad_x1 = max(p.x + p.w / 2 for p in self.pads)
        pad_y0 = min(p.y - p.h / 2 for p in self.pads)
        pad_y1 = max(p.y + p.h / 2 for p in self.pads)
        bx, by = self.body_w / 2, self.body_h / 2

        cx0 = grid(min(pad_x0, -bx) - CRT_MARGIN, 0.05)
        cx1 = grid(max(pad_x1, bx) + CRT_MARGIN, 0.05)
        cy0 = grid(min(pad_y0, -by) - CRT_MARGIN, 0.05)
        cy1 = grid(max(pad_y1, by) + CRT_MARGIN, 0.05)

        out = [
            f'(footprint "{self.name}"\n',
            "\t(version 20241229)\n",
            '\t(generator "pico-step-footprints")\n',
            '\t(layer "F.Cu")\n',
            f'\t(descr "{self.descr}")\n',
            f'\t(tags "{self.tags}")\n',
            self._text("Reference", "REF**", cy0 - 0.8, "F.SilkS"),
            self._text("Value", self.name, cy1 + 0.8, "F.Fab"),
            "\t(attr smd)\n",
        ]

        # Fab outline with a chamfer at pin 1.
        ch = min(1.0, self.body_w / 4)
        out.append(self._line(-bx + ch, -by, bx, -by, "F.Fab", FAB_W))
        out.append(self._line(bx, -by, bx, by, "F.Fab", FAB_W))
        out.append(self._line(bx, by, -bx, by, "F.Fab", FAB_W))
        out.append(self._line(-bx, by, -bx, -by + ch, "F.Fab", FAB_W))
        out.append(self._line(-bx, -by + ch, -bx + ch, -by, "F.Fab", FAB_W))
        for mx, my in self.fab_marks:
            out.append(self._line(mx - 0.5, my, mx + 0.5, my, "F.Fab", FAB_W))
            out.append(self._line(mx, my - 0.5, mx, my + 0.5, "F.Fab", FAB_W))

        out.append(self._rect(cx0, cy0, cx1, cy1, "F.CrtYd", CRT_W))

        # Silkscreen: segments of the body outline that clear the copper.
        clr = 0.2 + SILK_W / 2
        sy0, sy1 = -by - SILK_W, by + SILK_W
        sx0, sx1 = -bx - SILK_W, bx + SILK_W
        # An edge is drawn only when no pad reaches it, so silk never
        # overlaps copper.
        edges = (
            (sx0, sy0, sx1, sy0, lambda p: p.y - p.h / 2 <= sy0 + clr),
            (sx0, sy1, sx1, sy1, lambda p: p.y + p.h / 2 >= sy1 - clr),
            (sx0, sy0, sx0, sy1, lambda p: p.x - p.w / 2 <= sx0 + clr),
            (sx1, sy0, sx1, sy1, lambda p: p.x + p.w / 2 >= sx1 - clr),
        )
        for x1, y1, x2, y2, touches in edges:
            if not any(touches(p) for p in self.pads):
                out.append(self._line(x1, y1, x2, y2, "F.SilkS", SILK_W))
        # Pin 1 marker: small triangle outside the first pad.
        p1 = self.pads[0]
        tx, ty = p1.x - p1.w / 2 - 0.35, p1.y
        out.append(
            "\t(fp_poly (pts "
            f"(xy {num(tx)} {num(ty)}) (xy {num(tx - 0.3)} {num(ty - 0.25)}) "
            f"(xy {num(tx - 0.3)} {num(ty + 0.25)}))\n"
            f'\t\t(stroke (width {num(SILK_W)}) (type solid)) (fill yes) (layer "F.SilkS")\n'
            f'\t\t(uuid "{self._uid("pin1")}"))\n'
        )

        out.append(
            '\t(fp_text user "${REFERENCE}" (at 0 0 0) (layer "F.Fab")\n'
            f'\t\t(uuid "{self._uid("fabref")}")\n'
            "\t\t(effects (font (size 0.8 0.8) (thickness 0.12))))\n"
        )

        for p in self.pads:
            rr = " (roundrect_rratio 0.25)" if p.shape == "roundrect" else ""
            out.append(
                f'\t(pad "{p.number}" smd {p.shape} (at {num(p.x)} {num(p.y)}) '
                f"(size {num(p.w)} {num(p.h)}) "
                '(layers "F.Cu" "F.Mask" "F.Paste")' + rr + "\n"
                f'\t\t(uuid "{self._uid("pad", p.number, p.x, p.y)}"))\n'
            )

        if self.model:
            out.append(
                f'\t(model "{self.model}"\n'
                "\t\t(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n"
            )
        out.append(")\n")
        return "".join(out)


def dual_row(n: int, pitch: float, row_c2c: float, pad_w: float, pad_h: float) -> list[Pad]:
    """Gull-wing dual row, pin 1 top left, counter-clockwise numbering."""
    per_side = n // 2
    y0 = -(per_side - 1) * pitch / 2
    xl, xr = -row_c2c / 2, row_c2c / 2
    pads = [Pad(str(i + 1), xl, y0 + i * pitch, pad_w, pad_h) for i in range(per_side)]
    pads += [
        Pad(str(per_side + i + 1), xr, -y0 - i * pitch, pad_w, pad_h)
        for i in range(per_side)
    ]
    return pads


def pg_dso_8() -> Footprint:
    # Infineon TLE5012B data sheet Rev. 2.1, Figure 40 "Footprint of PG-DSO-8":
    # pad 1.31 x 0.65 mm, pitch 1.27 mm, 5.69 mm between pad row centers.
    # Body 3.9 x 4.9 mm. The sensing element is centered in the package
    # (Figure 39, +-200 um), marked with a cross on the fab layer.
    return Footprint(
        name="Infineon_PG-DSO-8",
        descr="Infineon PG-DSO-8 land pattern per TLE5012B data sheet Rev. 2.1 Figure 40",
        tags="Infineon PG-DSO-8 SOIC-8 TLE5012B",
        body_w=3.9,
        body_h=4.9,
        pads=dual_row(8, 1.27, 5.69, 1.31, 0.65),
        model="${KICAD9_3DMODEL_DIR}/Package_SO.3dshapes/SOIC-8_3.9x4.9mm_P1.27mm.step",
        fab_marks=[(0.0, 0.0)],
    )


def l_abracon_aota_b201610() -> Footprint:
    # Abracon AOTA-B201610S3R3-101-T data sheet Rev. A, "Recommended Land
    # Pattern": two 1.0 x 1.6 mm pads, 1.0 mm gap. Body 2.0 x 1.6 mm. The
    # part carries a polarity dot; pad 1 is the dot end, which the RP2350
    # regulator layout (RP2350 data sheet Figure 26) puts on VOUT, with
    # pad 2 on VREG_LX.
    return Footprint(
        name="L_Abracon_AOTA-B201610",
        descr="Abracon AOTA-B201610 2.0x1.6 mm polarity-marked inductor, pad 1 = dot",
        tags="inductor 2016 0806 Abracon AOTA RP2350",
        body_w=2.0,
        body_h=1.6,
        pads=[Pad("1", -1.0, 0.0, 1.0, 1.6), Pad("2", 1.0, 0.0, 1.0, 1.6)],
        model="${KICAD9_3DMODEL_DIR}/Inductor_SMD.3dshapes/L_Murata_DFE201610P.step",
    )


def vishay_powerpak_so8l_dual() -> Footprint:
    # Vishay "Recommended Minimum Pad for PowerPAK SO-8L Dual" (document
    # 63817, page 9 of the SQJB68EP data sheet). Package outline from
    # document 66934: body 4.90 x 4.37 mm (D1 x E1), leads L1 = 1.07 mm, so
    # the land pattern origin sits 0.18 mm below the body center; every y
    # here is shifted by +0.18 to center the body.
    #
    # Top view, leads at the bottom: pins 1..4 left to right are S1, G1, S2,
    # G2. Drain D1 is the left paddle (over pins 1-2), D2 the right one. The
    # paddles are numbered 6 (D1) and 5 (D2) to match KiCad's
    # Q_Dual_NMOS_S1G1S2G2D2D1 symbol. Each paddle is a 1.73 x 3.99 mm pad
    # plus two side tabs, all with the same number.
    dy = 0.18
    pads = [Pad(str(i + 1), -1.905 + 1.27 * i, 2.715 + dy, 0.41, 0.72) for i in range(4)]
    for num, s in (("6", -1), ("5", 1)):
        pads += [
            Pad(num, s * 1.115, -1.08 + dy, 1.73, 3.99, "rect"),
            Pad(num, s * 2.215, -2.87 + dy, 0.47, 0.41, "rect"),
            Pad(num, s * 2.2725, 0.0 + dy, 0.585, 0.51, "rect"),
        ]
    return Footprint(
        name="Vishay_PowerPAK_SO-8L_Dual",
        descr="Vishay PowerPAK SO-8L Dual, minimum pads per Vishay doc 63817 (SQJB68EP)",
        tags="Vishay PowerPAK SO-8L dual MOSFET SQJB68EP",
        body_w=4.90,
        body_h=4.37,
        pads=pads,
    )


FOOTPRINTS = [pg_dso_8, l_abracon_aota_b201610, vishay_powerpak_so8l_dual]

STOCK_FP_DIR = Path("/usr/share/kicad/footprints")

# Stock footprints copied into the project library with pads renumbered.
# KiCad library releases disagree on the USB-C shield pin: some name it S1
# in both symbol and footprint, others SH. The schematic symbol uses SH, so
# the project pins a footprint that matches it regardless of which library
# release is installed.
STOCK_COPIES = [
    (
        "Connector_USB.pretty/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
        "USB_C_Receptacle_GCT_USB4105-xx-A_16P_SH",
        {"S1": "SH"},
        None,
    ),
]


def copy_stock(src: str, name: str, renumber: dict[str, str], descr: str | None) -> str:
    text = (STOCK_FP_DIR / f"{src}.kicad_mod").read_text()
    if descr:
        text = re.sub(r'\(descr "[^"]*"\)', f'(descr "{descr}")', text, count=1)
    old = src.split("/")[-1]
    text = text.replace(f'(footprint "{old}"', f'(footprint "{name}"', 1)
    text = text.replace(f'(property "Value" "{old}"', f'(property "Value" "{name}"', 1)
    for a, b in renumber.items():
        text = text.replace(f'(pad "{a}"', f'(pad "{b}"')
    return text


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = [(fp.name, fp.render()) for fp in (make() for make in FOOTPRINTS)]
    outputs += [(name, copy_stock(src, name, ren, d)) for src, name, ren, d in STOCK_COPIES]
    for name, text in outputs:
        path = OUT_DIR / f"{name}.kicad_mod"
        path.write_text(text)
        print(f"wrote {path.relative_to(OUT_DIR.parent.parent)}")


if __name__ == "__main__":
    main()
