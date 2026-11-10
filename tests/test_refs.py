"""Reference designator checks.

The board is updated from the schematic and the DigiKey list is written by
hand, so both reference sets are compared with the schematic's to catch a
part added, removed or renamed in only one place.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def board_refs() -> set[str]:
    text = (ROOT / "pico-step.kicad_pcb").read_text()
    return set(re.findall(r'\(property "Reference" "([^"#][^"]*)"', text))


def schematic_refs(schematic: dict) -> set[str]:
    return {c["ref"] for c in schematic["components"]}


def test_board_refs_match_schematic(schematic):
    assert board_refs() == schematic_refs(schematic)


def test_digikey_list_covers_schematic(schematic):
    import csv

    with open(ROOT / "digikey_list.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    refs = [r for row in rows for r in row["Customer Reference"].split()]
    assert len(refs) == len(set(refs))
    assert sum(int(row["Quantity"]) for row in rows) == len(refs)
    assert set(refs) == schematic_refs(schematic)
