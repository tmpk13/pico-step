"""Reference designator checks.

Each board is updated from its schematic and the DigiKey list is written
by hand, so the reference sets are compared to catch a part added, removed
or renamed in only one place.
"""

from __future__ import annotations

import csv
import re

import pytest

from conftest import ROOT, board_file, stack_refs, uncut_copy


def board_refs(board: str) -> set[str]:
    text = board_file(board, ".kicad_pcb").read_text()
    return set(re.findall(r'\(property "Reference" "([^"#][^"]*)"', text))


def schematic_refs(schematic: dict) -> set[str]:
    return {c["ref"] for c in schematic["components"]}


def test_board_refs_match_schematic(board, schematic):
    if uncut_copy(board):
        pytest.skip(f"{board}: the board is still the uncut copy of the one-board "
                    "layout; this check runs once it is edited")
    assert board_refs(board) == schematic_refs(schematic)


def test_refs_differ_between_boards(schematics):
    # The stack sheet's parts are on every board; every other reference
    # names one part of the stack, so one order list and one assembly
    # drawing set can use it without saying which board it is on.
    seen: dict[str, str] = {}
    for board, sch in schematics.items():
        for ref in schematic_refs(sch) - stack_refs():
            assert ref not in seen, f"{ref} is on {seen[ref]} and {board}"
            seen[ref] = board


def test_digikey_list_covers_schematic(schematics):
    with open(ROOT / "digikey_list.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    refs = [r for row in rows for r in row["Customer Reference"].split()]
    assert len(refs) == len(set(refs))
    assert sum(int(row["Quantity"]) for row in rows) == len(refs)
    # The stack header's part depends on where its board sits in the stack
    # (pins below, a socket above, or a stacking socket for both), which is
    # not chosen yet, so the order list leaves it out.
    expected = set().union(*(schematic_refs(s) for s in schematics.values())) - stack_refs()
    assert set(refs) == expected
