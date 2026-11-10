"""Part comparison used when checking the tsch drawing against the hand schematic.

The tsch drawing is meant to describe the same board as the hand-placed
schematic, so a part present on one side only, or a value, footprint or MPN
that differs, must each be reported.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from parity import part_differences  # noqa: E402


def part(value="10k", footprint="Resistor_SMD:R_0603_1608Metric", mpn=""):
    return {"value": value, "footprint": footprint, "MPN": mpn}


def test_identical_parts_report_nothing():
    parts = {"R1": part(), "U1": part("RP2354A", "QFN", "SC1511-A4")}
    assert part_differences(parts, dict(parts)) == []


def test_missing_part_is_named_with_its_side():
    hand = {"R1": part(), "R2": part()}
    drawn = {"R1": part(), "R3": part()}
    assert part_differences(hand, drawn) == [
        "R2: only in the hand schematic",
        "R3: only in the tsch schematic",
    ]


def test_each_differing_field_gets_a_line():
    hand = {"C11": part("1u", "C_0603", "")}
    drawn = {"C11": part("4.7u", "C_0805", "GRM188")}
    assert part_differences(hand, drawn) == [
        "C11 value: hand '1u', tsch '4.7u'",
        "C11 footprint: hand 'C_0603', tsch 'C_0805'",
        "C11 MPN: hand '', tsch 'GRM188'",
    ]
