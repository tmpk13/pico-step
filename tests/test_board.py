"""Board against schematic.

`tools/pcb_sync.py` updates the board from the schematic; KiCad's DRC
schematic parity check confirms footprints, values, fields and pad nets
agree, the same comparison the GUI's "Update PCB from Schematic" makes.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_board_matches_schematic(tmp_path):
    out = tmp_path / "drc.json"
    subprocess.run(
        ["kicad-cli", "pcb", "drc", "--schematic-parity", "--format", "json",
         "-o", str(out), str(ROOT / "pico-step.kicad_pcb")],
        check=True, capture_output=True,
    )
    parity = json.loads(out.read_text())["schematic_parity"]
    assert parity == [], [(v["type"], v["description"]) for v in parity]
