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
    s = s[: m.end()] + '\n    (keepout "VM_pour" (%s))' % m.group(1) + s[m.end():]
    open(DSN, "w").write(s)
    print(f"wrote {DSN} with {s.count('(type fix)')} fixed wires and a VM keepout")
    return 0


if __name__ == "__main__":
    sys.exit(main())
