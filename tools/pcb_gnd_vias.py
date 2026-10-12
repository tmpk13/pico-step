#!/usr/bin/env python3
"""GND stitching vias for pico-step.kicad_pcb.

    python3 tools/pcb_gnd_vias.py grid            # via grid in the free spots
    python3 tools/pcb_gnd_vias.py pads build/drc.json   # via next to each GND pad the pour misses
    python3 tools/pcb_gnd_vias.py prune build/drc.json  # delete GND vias DRC reports as dangling

Dense routing cuts the GND pours into islands; the grid ties the islands
of both layers together, the pad mode rescues single pads, and prune
removes vias that ended up touching copper on one layer only. A spot is
used only if it keeps the default clearance from every other net's
copper, hole to hole 0.4 mm from any plated hole, stays out of the VM pour and 0.75 mm
from the edge and the mounting holes. Refill the zones and rerun DRC
after each step.
"""

from __future__ import annotations

import json
import math
import re
import sys

import pcbnew

BOARD = "pico-step.kicad_pcb"
VIA_SIZE, VIA_DRILL, TRACK_W, CLEAR = 0.5, 0.3, 0.25, 0.15
EDGE = (79.0, 79.0, 121.0, 121.0)
HOLES = [(84.5, 84.5), (115.5, 84.5), (84.5, 115.5), (115.5, 115.5)]
GRID = 1.5


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def seg_point_dist(ax, ay, bx, by, px, py) -> float:
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def pad_size(p: pcbnew.PAD) -> pcbnew.VECTOR2I:
    try:
        return p.GetSize(p.GetLayer())
    except TypeError:
        return p.GetSize()


class Checker:
    """Distance from a point to the nearest copper of another net, plus
    plated holes and the VM pour."""

    def __init__(self, board: pcbnew.BOARD, net: str):
        self.items = []     # (layer set, kind, geometry, half width)
        self.holes = []
        self.keepouts = []  # (x0, y0, x1, y1)
        both = {pcbnew.F_Cu, pcbnew.B_Cu}
        for f in board.GetFootprints():
            for p in f.Pads():
                pos = p.GetPosition()
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    self.holes.append((pos.x / 1e6, pos.y / 1e6, p.GetDrillSize().x / 1e6))
                if p.GetNetname() == net:
                    continue
                sz = pad_size(p)
                r = math.hypot(sz.x, sz.y) / 2e6     # bounding circle of the (rotated) pad
                layers = both if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else {p.GetLayer()}
                self.items.append((layers, "pt", (pos.x / 1e6, pos.y / 1e6), r))
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                pos = t.GetPosition()
                self.holes.append((pos.x / 1e6, pos.y / 1e6, t.GetDrill() / 1e6))
                if t.GetNetname() != net:
                    self.items.append((both, "pt", (pos.x / 1e6, pos.y / 1e6), t.GetWidth() / 2e6))
            elif t.GetNetname() != net:
                a, b = t.GetStart(), t.GetEnd()
                self.items.append(({t.GetLayer()}, "seg", (a.x / 1e6, a.y / 1e6, b.x / 1e6, b.y / 1e6), t.GetWidth() / 2e6))
        for z in board.Zones():
            if z.GetNetname() != net:
                bb = z.GetBoundingBox()
                self.keepouts.append((bb.GetX() / 1e6, bb.GetY() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6))

    def clearance(self, x: float, y: float, layers) -> float:
        best = 1e9
        for ls, kind, g, hw in self.items:
            if not (ls & layers):
                continue
            if kind == "pt":
                d = math.hypot(x - g[0], y - g[1]) - hw
            else:
                d = seg_point_dist(g[0], g[1], g[2], g[3], x, y) - hw
            best = min(best, d)
        return best

    def via_ok(self, x: float, y: float) -> bool:
        if not (EDGE[0] + 0.75 < x < EDGE[2] - 0.75 and EDGE[1] + 0.75 < y < EDGE[3] - 0.75):
            return False
        if any(math.hypot(x - hx, y - hy) < 1.65 + 0.5 + VIA_SIZE / 2 for hx, hy in HOLES):
            return False
        if any(x0 - 0.3 < x < x1 + 0.3 and y0 - 0.3 < y < y1 + 0.3 for x0, y0, x1, y1 in self.keepouts):
            return False
        if any(math.hypot(x - hx, y - hy) < hd / 2 + VIA_DRILL / 2 + 0.4 for hx, hy, hd in self.holes):
            return False
        return self.clearance(x, y, {pcbnew.F_Cu, pcbnew.B_Cu}) >= VIA_SIZE / 2 + CLEAR

    def add_via(self, x: float, y: float) -> None:
        self.items.append(({pcbnew.F_Cu, pcbnew.B_Cu}, "pt", (x, y), VIA_SIZE / 2))
        self.holes.append((x, y, VIA_DRILL))


def new_via(board: pcbnew.BOARD, net, x: float, y: float) -> None:
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    try:
        v.SetWidth(mm(VIA_SIZE))
    except TypeError:
        v.SetWidth(pcbnew.PADSTACK.ALL_LAYERS, mm(VIA_SIZE))
    v.SetDrill(mm(VIA_DRILL))
    v.SetNet(net)
    board.Add(v)


def grid(board: pcbnew.BOARD) -> int:
    chk = Checker(board, "GND")
    gnd = board.FindNet("GND")
    n = 0
    y = EDGE[1] + 1.0
    row = 0
    while y < EDGE[3] - 1.0:
        x = EDGE[0] + 1.0 + (GRID / 2 if row % 2 else 0)
        while x < EDGE[2] - 1.0:
            if chk.via_ok(x, y):
                new_via(board, gnd, x, y)
                chk.add_via(x, y)
                n += 1
            x += GRID
        y += GRID
        row += 1
    return n


def pads(board: pcbnew.BOARD, report: str) -> int:
    d = json.load(open(report))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    gnd = board.FindNet("GND")
    chk = Checker(board, "GND")
    done = set()
    n = 0
    for u in d["unconnected_items"]:
        for item in u["items"]:
            m = re.match(r"Pad (\S+) \[GND\] of (\S+) on (F|B)\.Cu", item["description"])
            if not m:
                continue
            num, ref, side = m.groups()
            if (ref, num) in done or ref not in fps:
                continue
            pad = next((p for p in fps[ref].Pads() if p.GetNumber() == num), None)
            if pad is None:
                continue
            layer = pcbnew.F_Cu if side == "F" else pcbnew.B_Cu
            px, py = pad.GetPosition().x / 1e6, pad.GetPosition().y / 1e6
            sz = pad_size(pad)
            reach = math.hypot(sz.x, sz.y) / 2e6 + VIA_SIZE / 2 + CLEAR + 0.1
            placed = False
            for dist in (reach, reach + 0.4, reach + 0.8, reach + 1.2):
                for k in range(8):
                    a = k * math.pi / 4
                    x, y = px + dist * math.cos(a), py + dist * math.sin(a)
                    if not chk.via_ok(x, y):
                        continue
                    if any(chk.clearance(px + (x - px) * i / 6, py + (y - py) * i / 6, {layer}) < TRACK_W / 2 + CLEAR
                           for i in range(1, 6)):
                        continue
                    new_via(board, gnd, x, y)
                    t = pcbnew.PCB_TRACK(board)
                    t.SetStart(pcbnew.VECTOR2I(mm(px), mm(py)))
                    t.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y)))
                    t.SetWidth(mm(TRACK_W))
                    t.SetLayer(layer)
                    t.SetNet(gnd)
                    board.Add(t)
                    chk.add_via(x, y)
                    done.add((ref, num))
                    n += 1
                    placed = True
                    break
                if placed:
                    break
            if not placed:
                print(f"no room for a via at {ref} pad {num}")
    return n


def prune(board: pcbnew.BOARD, report: str) -> int:
    d = json.load(open(report))
    spots = []
    for v in d["violations"]:
        if v["type"] == "via_dangling":
            for item in v["items"]:
                if "[GND]" in item["description"] and "pos" in item:
                    spots.append((item["pos"]["x"], item["pos"]["y"]))
    gone = 0
    for t in list(board.GetTracks()):
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != "GND" or t.IsLocked():
            continue
        pos = t.GetPosition()
        if any(abs(pos.x / 1e6 - x) < 0.01 and abs(pos.y / 1e6 - y) < 0.01 for x, y in spots):
            board.Delete(t)
            gone += 1
    # tracks that led only to a deleted via
    for t in list(board.GetTracks()):
        if t.GetClass() == "PCB_TRACK" and t.GetNetname() == "GND" and not t.IsLocked():
            e = t.GetEnd()
            if any(abs(e.x / 1e6 - x) < 0.01 and abs(e.y / 1e6 - y) < 0.01 for x, y in spots):
                board.Delete(t)
    return gone


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "grid"
    report = sys.argv[2] if len(sys.argv) > 2 else "build/drc.json"
    board = pcbnew.LoadBoard(BOARD)
    if mode == "grid":
        n = grid(board)
        print(f"added {n} grid vias")
    elif mode == "pads":
        n = pads(board, report)
        print(f"added {n} pad vias")
    elif mode == "prune":
        n = prune(board, report)
        print(f"removed {n} dangling vias")
    else:
        print("mode: grid | pads <drc.json> | prune <drc.json>")
        return 1
    pcbnew.SaveBoard(BOARD, board)
    return 0


if __name__ == "__main__":
    sys.exit(main())
