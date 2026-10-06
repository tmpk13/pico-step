"""Reference designator checks.

The schematic and board are edited in the KiCad GUI as well as generated, so
their reference sets are compared with the generator to catch a rename made
in only one place.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def circuit() -> dict:
    out = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "circuit.py")],
        check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out)


def refs_in(path: Path) -> set[str]:
    text = path.read_text()
    # Schematic instances carry the placed reference; the Reference property
    # in its embedded library symbols is only the prefix ("C", "R").
    if path.suffix == ".kicad_sch":
        return set(re.findall(r'\(reference "([^"#][^"]*)"\)', text))
    return set(re.findall(r'\(property "Reference" "([^"#][^"]*)"', text))


@pytest.mark.parametrize("board_file", ["pico-step.kicad_sch", "pico-step.kicad_pcb"])
def test_kicad_refs_match_generator(circuit, board_file):
    gen = {c["ref"] for c in circuit["components"]}
    assert refs_in(ROOT / board_file) == gen


def test_digikey_list_covers_generator(circuit):
    import csv

    with open(ROOT / "digikey_list.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    refs = [r for row in rows for r in row["Customer Reference"].split()]
    assert len(refs) == len(set(refs))
    assert sum(int(row["Quantity"]) for row in rows) == len(refs)
    assert set(refs) == {c["ref"] for c in circuit["components"]}
