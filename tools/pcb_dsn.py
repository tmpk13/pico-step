#!/usr/bin/env python3
"""Export build/pico-step.dsn for freerouting.

KiCad writes copper zones as Specctra planes. Freerouting treats a plane
as copper of its net but still routes other nets across it, which would
cut the VM pour, so the pour's outline is added again as a keepout.
    python3 tools/pcb_dsn.py
"""

import re
import sys

import pcbnew

BOARD = "pico-step.kicad_pcb"
DSN = "build/pico-step.dsn"


def main() -> int:
    board = pcbnew.LoadBoard(BOARD)
    if not pcbnew.ExportSpecctraDSN(board, DSN):
        print("export failed")
        return 1
    s = open(DSN).read()
    m = re.search(r"\(plane VM \((polygon B\.Cu 0[^)]*)\)\s*\)", s)
    if not m:
        print("no VM plane in the export")
        return 1
    extra = ['    (keepout "VM_pour" (%s))' % m.group(1)]
    # The router keeps no edge clearance from the outline circles of the
    # mounting holes or the outer edge, so add 0.5 mm keepouts there.
    for i, (x, y) in enumerate([(84.5, 84.5), (115.5, 84.5), (84.5, 115.5), (115.5, 115.5)]):
        for layer in ("F.Cu", "B.Cu"):
            extra.append('    (keepout "hole%d%s" (circle %s 4400 %d %d))' % (i, layer[0], layer, x * 1000, -y * 1000))
    s = s[: m.end()] + "\n" + "\n".join(extra) + s[m.end():]
    s, n = re.subn(r"\(boundary\s*\(path pcb 0[^()]*\)\s*\)",
                   "(boundary (path pcb 0 79500 -79500 120500 -79500 120500 -120500 79500 -120500 79500 -79500))", s, count=1)
    if n != 1:
        print("warning: board outline not shrunk for the edge clearance")
    open(DSN, "w").write(s)
    print(f"wrote {DSN} with {s.count('(type fix)')} fixed wires and a VM keepout")
    return 0


if __name__ == "__main__":
    sys.exit(main())
