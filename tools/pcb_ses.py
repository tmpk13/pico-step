#!/usr/bin/env python3
"""Import a freerouting session file into pico-step.kicad_pcb.

    python3 tools/pcb_ses.py build/pico-step.ses
The pre-routed, locked copper is exported to the DSN as fixed wiring and
comes back unchanged; only the autorouted tracks and vias are new.
"""

import sys

import pcbnew

BOARD = "pico-step.kicad_pcb"


def main() -> int:
    ses = sys.argv[1] if len(sys.argv) > 1 else "build/pico-step.ses"
    board = pcbnew.LoadBoard(BOARD)
    before = len(board.GetTracks())
    if not pcbnew.ImportSpecctraSES(board, ses):
        print("import failed")
        return 1
    pcbnew.SaveBoard(BOARD, board)
    print(f"tracks and vias: {before} -> {len(board.GetTracks())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
