#!/usr/bin/env python3
"""Apply the hand-planned footprint placement to pico-step.kicad_pcb.

The board is a 42.2 mm square that mounts on the back of a NEMA17 motor
(31 mm hole spacing); the angle sensor U3 sits on the back side at the
shaft axis. Coordinates are board millimeters, rotation in degrees, layer
F or B. Run from the project root:
    python3 tools/pcb_place.py [--check]
--check only reports footprints whose position differs from the table.
"""

from __future__ import annotations

import sys

import pcbnew

BOARD = "pico-step.kicad_pcb"

# ref: (x, y, rot, layer)
PLACEMENT: dict[str, tuple[float, float, float, str]] = {
    # ---- connectors and buttons (edges) ---------------------------------
    "J4": (97.00, 82.00, 0, "F"),        # motor, top edge
    "SW1": (90.50, 82.15, 90, "F"),      # BOOTSEL, top left corner
    "SW2": (109.90, 82.15, 90, "F"),     # RESET, top right corner
    "J1": (117.25, 92.80, 90, "F"),      # USB-C, right edge beside the FET row
    "J2": (95.60, 115.35, 180, "F"),    # VM screw terminal, bottom edge
    "J3": (106.70, 119.30, 90, "F"),     # SWD, bottom edge right
    "D1": (108.30, 114.00, 90, "F"),
    "R8": (106.30, 114.00, 90, "F"),
    # ---- angle sensor, back side at the shaft axis ----------------------
    "U3": (100.00, 100.00, 180, "B"),
    "C18": (95.30, 100.00, 90, "B"),
    "R9": (93.00, 100.20, 90, "B"),
    "R10": (93.00, 104.00, 90, "B"),
    "R11": (91.00, 100.20, 90, "B"),
    "R14": (91.00, 104.00, 90, "B"),
    # ---- power stage ------------------------------------------------------
    # FET row under the motor connector, leads toward the driver.
    "Q3": (90.20, 89.80, 0, "F"),        # phase B, half bridge 1
    "Q4": (96.40, 89.80, 0, "F"),        # phase B, half bridge 2
    "Q1": (102.60, 89.80, 0, "F"),       # phase A, half bridge 1
    "Q2": (108.80, 89.80, 0, "F"),       # phase A, half bridge 2
    "R18": (94.60, 97.00, 0, "F"),       # RSENSE B, hot end left
    "R15": (108.50, 96.30, 0, "F"),      # RSENSE A, hot end left
    "U5": (103.90, 105.00, 0, "F"),     # thermal vias clear of U3 on the back
    "C19": (85.00, 103.20, 90, "F"),     # J2 side bulk, left edge
    "C35": (115.30, 106.50, -90, "F"),   # VM bulk, right edge, VM pad up
    "C34": (84.40, 94.60, -90, "B"),     # bridge B VM decoupling, VM pad up
    "C33": (107.20, 99.60, -90, "B"),   # bridge A VM decoupling below R15, VM pad up
    "C32": (100.50, 95.00, 90, "B"),     # bootstrap CB2
    "C29": (111.90, 97.50, 90, "B"),     # bootstrap CA1
    # left of U5 (top)
    "C31": (97.10, 100.40, 0, "F"),      # bootstrap CB1
    "C25": (96.60, 103.60, 90, "F"),     # 12VOUT
    "C21": (97.10, 107.50, 0, "F"),      # VS, VM pad left
    "C27": (92.50, 107.80, 0, "F"),      # 5VOUT
    "R20": (92.50, 103.90, 0, "F"),      # 47R SRAL
    "R22": (92.50, 105.80, 0, "F"),      # 47R SRBL
    "R19": (92.50, 100.10, 0, "F"),      # 47R SRAH
    "R21": (92.50, 102.00, 0, "F"),      # 47R SRBH
    "R23": (105.80, 108.30, 0, "B"),     # 2.2R 5VOUT-VCC, below the U5 back pad
    # below U5 (top)
    "C26": (103.00, 111.10, 0, "F"),    # VCC_IO
    "R25": (106.40, 111.10, 0, "F"),    # SD_MODE pull-down
    # right of U5 (back side)
    "C30": (109.80, 100.50, 90, "B"),   # bootstrap CA2
    "C23": (111.90, 100.70, -90, "B"),   # VCP-VS, VM pad up
    "C22": (109.70, 105.60, -90, "B"),   # VSA, VM pad up
    "C24": (111.90, 103.80, 90, "B"),    # CPI-CPO
    "C28": (111.90, 106.90, 90, "B"),    # VCC
    "R24": (113.80, 101.00, 90, "B"),    # ENN pull-up
    "R16": (115.60, 109.50, 90, "B"),    # DIAG0 pull-up
    "R17": (113.80, 104.50, 90, "B"),    # DIAG1 pull-up
    "R26": (107.90, 104.50, 90, "B"),    # 1k ENCN
    # ---- MCU block, back side -------------------------------------------
    "U1": (104.00, 113.30, 90, "B"),     # SPI pins on the bottom edge
    "C12": (110.60, 109.30, 0, "B"),     # COUT
    "L1": (110.00, 111.50, 180, "B"),    # LX pad toward pin 48
    "R27": (113.60, 108.80, 90, "B"),
    "C11": (109.70, 113.80, 0, "B"),     # CIN
    "C17": (112.70, 111.90, 90, "B"),    # VREG_AVDD
    "C9": (109.70, 115.70, 0, "B"),
    "C7": (93.00, 119.80, 0, "B"),
    "C8": (108.10, 107.60, 90, "B"),
    "C14": (100.50, 105.40, 90, "B"),   # +1V1 near pin 39
    "C6": (97.90, 110.30, 0, "B"),
    "C36": (95.40, 108.60, 90, "B"),     # +1V1 near pin 23
    "C15": (100.30, 117.60, 0, "F"),     # crystal on the top side, vias to pins 21/22
    "Y1": (101.30, 114.50, 0, "F"),
    "C5": (95.50, 111.70, 90, "B"),
    "C16": (103.30, 117.60, 0, "F"),
    "C10": (93.00, 116.90, 90, "B"),
    "R5": (104.50, 114.50, 90, "F"),
    "C3": (96.10, 119.60, 0, "B"),
    "C4": (99.20, 119.60, 0, "B"),
    "C13": (102.30, 119.60, 0, "B"),     # +1V1 near pin 6
    "R3": (110.00, 117.40, 0, "B"),      # USB series at U1
    "R4": (112.40, 117.00, 90, "B"),
    "R6": (90.50, 80.70, 0, "B"),        # BOOTSEL 1k under SW1
    "R7": (109.90, 80.70, 0, "B"),       # RUN pull-up under SW2
    "R12": (90.80, 111.50, 0, "B"),      # VM sense divider at J2 pin 1
    "R13": (90.80, 113.20, 0, "B"),
    "C20": (90.80, 109.80, 0, "B"),
    # ---- USB power, back side under J1 -----------------------------------
    "R1": (116.30, 91.50, 90, "B"),
    "R2": (116.30, 94.80, 90, "B"),
    "U2": (116.80, 100.30, 0, "B"),
    "C2": (116.80, 103.40, 0, "B"),
    "C1": (116.80, 106.00, 0, "B"),
}


def apply(board: pcbnew.BOARD, check: bool = False) -> int:
    moved = 0
    refs = {f.GetReference(): f for f in board.GetFootprints()}
    missing = sorted(set(refs) - set(PLACEMENT))
    if missing:
        print("not in table:", " ".join(missing))
    for ref, (x, y, rot, layer) in PLACEMENT.items():
        f = refs.get(ref)
        if f is None:
            print("not on board:", ref)
            continue
        want_layer = pcbnew.B_Cu if layer == "B" else pcbnew.F_Cu
        pos = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        same = (f.GetPosition() == pos and f.GetLayer() == want_layer
                and abs(f.GetOrientationDegrees() - rot) < 0.01)
        if same:
            continue
        moved += 1
        if check:
            p = f.GetPosition()
            print(f"{ref}: at ({p.x/1e6:.2f},{p.y/1e6:.2f}) rot {f.GetOrientationDegrees():.0f}"
                  f" {board.GetLayerName(f.GetLayer())}, table says ({x},{y}) rot {rot} {layer}")
            continue
        if f.GetLayer() != want_layer:
            f.SetLayerAndFlip(want_layer)
        f.SetPosition(pos)
        f.SetOrientationDegrees(rot)
    return moved


def main() -> int:
    check = "--check" in sys.argv
    board = pcbnew.LoadBoard(BOARD)
    moved = apply(board, check)
    if check:
        print(f"{moved} footprints differ")
        return 1 if moved else 0
    if moved:
        pcbnew.SaveBoard(BOARD, board)
    print(f"{moved} footprints moved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
