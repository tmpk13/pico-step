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
    # the session repeats the fixed wiring; drop those unlocked copies
    locked = set()
    for t in board.GetTracks():
        if t.IsLocked():
            locked.add((t.GetClass(), t.GetLayer(), tuple(t.GetStart()), tuple(t.GetEnd())))
    dups = [t for t in board.GetTracks() if not t.IsLocked()
            and (t.GetClass(), t.GetLayer(), tuple(t.GetStart()), tuple(t.GetEnd())) in locked]
    for t in dups:
        board.Delete(t)
    pcbnew.SaveBoard(BOARD, board)
    print(f"tracks and vias: {before} -> {len(board.GetTracks())} ({len(dups)} duplicates of fixed wiring dropped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
