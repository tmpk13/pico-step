"""Each board against its schematic.

`tools/pcb_sync.py BOARD` updates a board from its schematic; KiCad's DRC
schematic parity check confirms footprints, values, fields and pad nets
agree, the same comparison the GUI's "Update PCB from Schematic" makes.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from conftest import board_file, uncut_copy


def test_board_matches_schematic(board, tmp_path):
    if uncut_copy(board):
        pytest.skip(f"{board}: the board is still the uncut copy of the one-board "
                    "layout; this check runs once it is edited")
    out = tmp_path / "drc.json"
    subprocess.run(
        ["kicad-cli", "pcb", "drc", "--schematic-parity", "--format", "json",
         "-o", str(out), str(board_file(board, ".kicad_pcb"))],
        check=True, capture_output=True,
    )
    parity = json.loads(out.read_text())["schematic_parity"]
    assert parity == [], [(v["type"], v["description"]) for v in parity]
