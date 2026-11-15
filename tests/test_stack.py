"""The boards join only through the stack header.

Each board is its own KiCad project, so a global label or power port of
the same name on two boards is two separate nets. Nothing joins them
unless both reach a pin of the stack header, and neither tsch nor ERC can
see across projects.
"""

from __future__ import annotations

from conftest import stack_refs


def named_nets(schematic: dict) -> dict[str, set[str]]:
    """Nets named by a global label or power port. KiCad gives a local
    label the sheet path ("/driver/OUT1A") and an unlabeled net a pin name
    ("Net-(U5-VCP)"); both stay on their board."""
    return {n["name"]: set(n["pins"]) for n in schematic["nets"]
            if not n["name"].startswith(("/", "Net-("))}


def test_nets_shared_by_boards_reach_the_stack_header(schematics):
    stack = stack_refs()
    nets = {b: named_nets(s) for b, s in schematics.items()}
    for name in sorted(set().union(*nets.values())):
        on = [b for b in nets if name in nets[b]]
        if len(on) < 2:
            continue
        for board in on:
            pins = nets[board][name]
            assert any(p.split(".")[0] in stack for p in pins), \
                f"{name} is on {', '.join(on)} but misses the stack header on {board}"


def test_every_board_carries_the_stack_header(schematics):
    for board, sch in schematics.items():
        refs = {c["ref"] for c in sch["components"]}
        assert stack_refs() <= refs, board
