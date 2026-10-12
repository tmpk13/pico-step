#!/usr/bin/env python3
"""Pre-route the power stage of pico-step.kicad_pcb.

Adds, as locked items, the copper that carries motor current: the FET
source-to-drain links, the half bridge outputs to the motor connector,
the sense resistor links, the VM pour on the back with vias into the
FET drain paddles, and the VM feeds to the driver supply pins. A
Specctra export carries locked items as fixed wiring, so the autorouter
keeps them. Run after tools/pcb_place.py and before autorouting; it
first removes every track, via and VM zone on the board.
    python3 tools/pcb_route.py
Coordinates are board millimeters. Pad positions are read from the
board so small placement moves of the parts named here carry over.
"""

from __future__ import annotations

import sys

import pcbnew

BOARD = "pico-step.kicad_pcb"
F = pcbnew.F_Cu
B = pcbnew.B_Cu


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def pt(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(mm(x), mm(y))


class Router:
    def __init__(self, board: pcbnew.BOARD):
        self.board = board
        self.fps = {f.GetReference(): f for f in board.GetFootprints()}

    def net(self, name: str) -> pcbnew.NETINFO_ITEM:
        n = self.board.FindNet(name)
        assert n is not None, f"no net {name}"
        return n

    def pads(self, ref: str, number: str) -> list[pcbnew.PAD]:
        ps = [p for p in self.fps[ref].Pads() if p.GetNumber() == number]
        assert ps, f"no pad {ref}.{number}"
        return ps

    def pad(self, ref: str, number: str) -> tuple[float, float, str]:
        p = self.pads(ref, number)[0]
        pos = p.GetPosition()
        return pos.x / 1e6, pos.y / 1e6, p.GetNetname()

    def track(self, layer: int, points, width: float, netname: str) -> None:
        net = self.net(netname)
        for a, b in zip(points, points[1:]):
            t = pcbnew.PCB_TRACK(self.board)
            t.SetStart(pt(*a))
            t.SetEnd(pt(*b))
            t.SetWidth(mm(width))
            t.SetLayer(layer)
            t.SetNet(net)
            t.SetLocked(True)
            self.board.Add(t)

    def via(self, x: float, y: float, netname: str, size: float = 0.8, drill: float = 0.4) -> None:
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(pt(x, y))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        try:
            v.SetWidth(mm(size))
        except TypeError:
            v.SetWidth(pcbnew.PADSTACK.ALL_LAYERS, mm(size))
        v.SetDrill(mm(drill))
        v.SetNet(self.net(netname))
        v.SetLocked(True)
        self.board.Add(v)

    def zone(self, layer: int, points, netname: str, name: str, priority: int,
             clearance: float, min_thickness: float) -> None:
        z = pcbnew.ZONE(self.board)
        z.SetLayer(layer)
        z.SetNet(self.net(netname))
        z.SetZoneName(name)
        z.SetAssignedPriority(priority)
        z.SetLocalClearance(mm(clearance))
        z.SetMinThickness(mm(min_thickness))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        outline = z.Outline()
        outline.NewOutline()
        for x, y in points:
            outline.Append(mm(x), mm(y))
        z.SetLocked(True)
        self.board.Add(z)


def gnd_zone_settings(board: pcbnew.BOARD) -> None:
    """Tighten the GND pour so it reaches pads between dense traces."""
    for z in board.Zones():
        if z.GetNetname() == "GND":
            z.SetLocalClearance(mm(0.25))
            z.SetMinThickness(mm(0.25))
            z.SetThermalReliefGap(mm(0.3))
            z.SetThermalReliefSpokeWidth(mm(0.3))


def clear(board: pcbnew.BOARD) -> None:
    for t in list(board.GetTracks()):
        board.Delete(t)
    for z in list(board.Zones()):
        if z.GetNetname() == "VM":
            board.Delete(z)


def fix_thermal_vias(r: Router) -> int:
    """The TQFP-48 ThermalVias footprint uses 0.2 mm drills; the board
    rules and the fab want 0.3 mm, so widen them in place."""
    n = 0
    for p in r.pads("U5", "49"):
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            p.SetDrillSize(pcbnew.VECTOR2I(mm(0.3), mm(0.3)))
            size = pcbnew.VECTOR2I(mm(0.6), mm(0.6))
            try:
                p.SetSize(size)
            except TypeError:
                p.SetSize(pcbnew.PADSTACK.ALL_LAYERS, size)
            n += 1
    return n


# Half bridges left to right under the motor connector: Q3 (1B), Q4 (2B),
# Q1 (1A), Q2 (2A). Phase A outputs go to J4 on the top layer, phase B on
# the back, because J4 pin order is 1A 2A 1B 2B and the pairs cross.
FETS = ["Q3", "Q4", "Q1", "Q2"]
Y_RUN = 85.4      # output run above each FET, below the J4 pads
X_LINK = 3.1      # link column left of the FET center, between neighbors


def fet_geometry(r: Router, q: str) -> dict:
    fp = r.fps[q]
    cx = fp.GetPosition().x / 1e6
    tabs5 = sorted(r.pads(q, "5"), key=lambda p: p.GetPosition().y)
    tab = tabs5[0].GetPosition()                       # D2 top tab
    paddle6 = max(r.pads(q, "6"), key=lambda p: p.GetSize().y)
    pad6 = paddle6.GetPosition()
    p1 = r.pad(q, "1")
    p3 = r.pad(q, "3")
    return {"cx": cx, "xl": cx - X_LINK, "p1": p1, "p3": p3,
            "tab": (tab.x / 1e6, tab.y / 1e6), "pad6": (pad6.x / 1e6, pad6.y / 1e6),
            "out": p1[2], "sense": p3[2]}


def route_fets(r: Router) -> None:
    g = {q: fet_geometry(r, q) for q in FETS}
    for q in FETS:
        d = g[q]
        x1, y1, out = d["p1"]
        xl, (tx, ty) = d["xl"], d["tab"]
        # S1 lead around the left side of the package to the D2 paddle tab
        r.track(F, [(x1, y1), (xl, y1), (xl, Y_RUN)], 0.5, out)
        r.track(F, [(xl, Y_RUN), (tx, Y_RUN)], 0.6, out)
        r.track(F, [(tx, Y_RUN), (tx, ty)], 0.45, out)
        # VM into the D1 paddle from the pour on the back
        px, py = d["pad6"]
        r.via(px, py - 0.75, "VM")
        r.via(px, py + 0.75, "VM")

    j4 = {n: r.pad("J4", n) for n in "1234"}
    # phase A on the top: 1A to J4.1, 2A to J4.2
    xl = g["Q1"]["xl"]
    jx, jy, _ = j4["1"]
    r.track(F, [(xl, Y_RUN), (xl, 84.5), (jx, 84.5), (jx, jy)], 0.6, g["Q1"]["out"])
    xl = g["Q2"]["xl"]
    jx, jy, _ = j4["2"]
    r.track(F, [(xl, Y_RUN), (xl, 83.6), (jx, 83.6), (jx, jy)], 0.6, g["Q2"]["out"])
    # phase B on the back: 1B to J4.3, 2B to J4.4
    xv = g["Q3"]["xl"] + 0.3
    jx, jy, _ = j4["3"]
    r.via(xv, Y_RUN, g["Q3"]["out"])
    r.track(B, [(xv, Y_RUN), (xv, 84.2), (jx, 84.2), (jx, jy)], 0.8, g["Q3"]["out"])
    xv = g["Q4"]["xl"] + 0.3
    jx, jy, _ = j4["4"]
    r.via(xv, Y_RUN, g["Q4"]["out"])
    r.track(B, [(xv, Y_RUN), (jx, Y_RUN), (jx, jy)], 0.8, g["Q4"]["out"])

    # low side sources to the sense resistors
    rbx, rby, sb = r.pad("R18", "1")
    rax, ray, sa = r.pad("R15", "1")
    x3, y3, _ = g["Q3"]["p3"]
    r.track(F, [(x3, y3), (x3, 94.3), (rbx, 95.1), (rbx, rby)], 0.8, sb)
    x3, y3, _ = g["Q4"]["p3"]
    r.track(F, [(x3, y3), (x3, 93.6)], 0.4, sb)
    r.via(x3, 93.6, sb, 0.8, 0.4)
    r.track(B, [(x3, 93.6), (x3, 94.6), (rbx, 96.6), (rbx, rby)], 0.8, sb)
    r.via(rbx, rby, sb, 1.0, 0.5)
    x3, y3, _ = g["Q1"]["p3"]
    r.track(F, [(x3, y3), (x3, 93.6)], 0.4, sa)
    r.via(x3, 93.6, sa, 0.8, 0.4)
    r.track(B, [(x3, 93.6), (x3, 95.5), (rax, 95.5), (rax, ray)], 0.8, sa)
    r.via(rax, ray, sa, 1.0, 0.5)
    x3, y3, _ = g["Q2"]["p3"]
    r.track(F, [(x3, y3), (x3, 93.6)], 0.4, sa)
    r.via(x3, 93.6, sa, 0.8, 0.4)
    r.track(B, [(x3, 93.6), (x3, 95.5), (rax, 95.5)], 0.8, sa)


def route_vm(r: Router) -> None:
    # pour under the FET row with arms down to the bridge capacitors
    r.zone(B, [(85.8, 86.6), (113.6, 86.6), (113.6, 93.1), (88.2, 93.1),
               (88.2, 96.6), (86.0, 96.6), (86.0, 95.0), (83.0, 95.0),
               (83.0, 92.8), (85.8, 92.8)], "VM", "VM", 1, 0.25, 0.3)
    # left feed: pour -> VS pin 4 and its capacitor C21
    c21x, c21y, _ = r.pad("C21", "1")
    p4x, p4y, _ = r.pad("U5", "4")
    # along the back under the sensor resistors to a via right at pin 4,
    # with a branch to the VS capacitor C21
    r.track(B, [(87.0, 96.3), (87.0, 104.05), (98.0, 104.05), (98.4, p4y)], 0.8, "VM")
    r.via(98.4, p4y, "VM")
    r.track(F, [(98.4, p4y), (p4x - 0.4, p4y)], 0.3, "VM")
    r.track(B, [(95.0, 104.05), (95.0, 106.3)], 0.6, "VM")
    r.via(95.0, 106.3, "VM")
    r.track(F, [(95.0, 106.3), (c21x, c21y)], 0.5, "VM")
    # right feed: pour -> C33, C23, C22, VSA pin 33 and the bulk cap C35
    c23x, c23y, _ = r.pad("C23", "1")
    c22x, c22y, _ = r.pad("C22", "1")
    p33x, p33y, _ = r.pad("U5", "33")
    c35x, _, _ = r.pad("C35", "1")
    c33x, c33y, _ = r.pad("C33", "1")
    # Out of the pour through a via at its right end, then down the top
    # layer between R15 and J1 (the back there must stay open for the
    # charge pump parts), into a via that touches C23's VM pad, and on
    # to VSA, C22 and C35.
    r.via(112.2, 92.6, "VM")
    r.track(F, [(112.2, 92.6), (112.55, 93.3), (112.55, 99.0), (112.9, 99.5)], 0.5, "VM")
    r.via(112.9, 99.5, "VM")                       # touches C22's VM pad on the back
    r.track(B, [(112.9, 99.5), (c22x, c22y)], 0.5, "VM")
    r.track(F, [(112.9, 99.5), (112.9, 108.1), (110.3, 108.1)], 0.8, "VM")
    r.via(110.3, 108.1, "VM")                      # touches C23's VM pad on the back
    r.track(B, [(110.3, 108.1), (c23x, c23y)], 0.5, "VM")
    r.track(F, [(112.9, p33y), (p33x + 0.55, p33y)], 0.3, "VM")
    r.track(F, [(112.9, p33y), (c35x - 1.0, p33y)], 1.0, "VM")
    r.track(B, [(112.9, 99.5), (112.3, 99.5), (111.3, 98.6), (c33x, c33y)], 0.5, "VM")


def route_j2(r: Router) -> None:
    """Terminal block pin 1 to its bulk capacitor; this net is not VM in
    the schematic (see the Power? note), so it stays separate here."""
    jx, jy, net = r.pad("J2", "1")
    cx, cy, _ = r.pad("C19", "1")
    r.track(F, [(jx, jy), (jx, 110.6), (cx + 1.0, 110.6), (cx, cy + 1.4)], 1.0, net)


def main() -> int:
    board = pcbnew.LoadBoard(BOARD)
    clear(board)
    r = Router(board)
    gnd_zone_settings(board)
    n = fix_thermal_vias(r)
    route_fets(r)
    route_vm(r)
    route_j2(r)
    pcbnew.SaveBoard(BOARD, board)
    print(f"thermal vias widened: {n}, tracks and vias: {len(board.GetTracks())}, zones: {len(board.Zones())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
