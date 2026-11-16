"""The boards join only through the stack header.

Each board is its own KiCad project, so a global label or power port of
the same name on two boards is two separate nets. Nothing joins them
unless both reach a pin of the stack header, and neither tsch nor ERC can
see across projects.
"""

from __future__ import annotations

import math
import re

import pytest

from conftest import BOARDS, board_file, stack_refs, uncut_copy


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


def stack_header_pads(board: str) -> dict[str, tuple[float, float]]:
    """"J5.1" -> board position in mm of every stack header pad, as seen
    from the top (y points down). A .kicad_pcb gives pad positions relative
    to their footprint, already mirrored for a footprint on the back, and
    the footprint angle turns them counterclockwise on screen."""
    text = board_file(board, ".kicad_pcb").read_text()
    starts = [m.start() for m in re.finditer(r'\(footprint\s+"', text)]
    pads = {}
    for a, b in zip(starts, starts[1:] + [len(text)]):
        block = text[a:b]
        ref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        if not ref or ref.group(1) not in stack_refs():
            continue
        x, y, angle = re.search(
            r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\s*\)', block).groups()
        t = math.radians(float(angle or 0))
        for m in re.finditer(r'\(pad\s+"([^"]+)"[^(]*\(at\s+([-\d.]+)\s+([-\d.]+)', block):
            px, py = float(m.group(2)), float(m.group(3))
            pads[f"{ref.group(1)}.{m.group(1)}"] = (
                float(x) + px * math.cos(t) + py * math.sin(t),
                float(y) - px * math.sin(t) + py * math.cos(t))
    return pads


def test_stack_headers_line_up_on_every_cut_board():
    """The header pins pass through every board, so each pad sits at the
    same spot on each board, whichever side the header is fitted on."""
    cut = [b for b in BOARDS if not uncut_copy(b)]
    if len(cut) < 2:
        pytest.skip(f"only {', '.join(cut) or 'no board'} is cut so far")
    first = stack_header_pads(cut[0])
    for board in cut[1:]:
        pads = stack_header_pads(board)
        assert pads.keys() == first.keys(), board
        for pad, (x, y) in first.items():
            assert math.dist(pads[pad], (x, y)) < 0.01, f"{pad} on {board}"


def test_stack_headers_keep_the_routing_orientation(board):
    """The stack pinout puts each line where its chip's pins leave toward
    it, which holds only with the headers as the stack sheet describes
    them, seen from the top: J5's odd row and J6's even row face each
    other (the board center), and pin numbers rise from left to right."""
    if uncut_copy(board):
        pytest.skip(f"{board}: the board is still the uncut copy of the one-board "
                    "layout; this check runs once it is edited")
    pads = stack_header_pads(board)

    def center(ref):
        points = [p for name, p in pads.items() if name.startswith(ref + ".")]
        return (sum(p[0] for p in points) / len(points),
                sum(p[1] for p in points) / len(points))

    for ref, other, inner in (("J5", "J6", 1), ("J6", "J5", 0)):
        target = center(other)
        for col in range(6):
            odd, even = pads[f"{ref}.{2 * col + 1}"], pads[f"{ref}.{2 * col + 2}"]
            near, far = (odd, even) if inner else (even, odd)
            assert math.dist(near, target) < math.dist(far, target), \
                f"{ref} pins {2 * col + 1}/{2 * col + 2}: the signal row faces away from {other}"
        assert pads[f"{ref}.1"][0] < pads[f"{ref}.11"][0], f"{ref}: pin 1 is not on the left"
