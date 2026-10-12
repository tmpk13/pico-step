#!/usr/bin/env python3
"""Refill every zone of pico-step.kicad_pcb and save it.

kicad-cli DRC checks the zone fill stored in the file, so run this after
any script that adds copper and before DRC or export.
    python3 tools/pcb_fill.py
"""

import sys

import pcbnew

BOARD = "pico-step.kicad_pcb"


def main() -> int:
    board = pcbnew.LoadBoard(BOARD)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    print(f"filled {len(board.Zones())} zones")
    return 0


if __name__ == "__main__":
    sys.exit(main())
