#!/usr/bin/env python3
"""Update pico-step.kicad_pcb from the schematic, keeping the placement.

Does what "Update PCB from Schematic" does for this board, from the
command line: footprints whose symbol is gone are deleted, a footprint
whose library id changed is swapped in at the same position, side and
rotation, values, symbol fields and symbol links (paths) follow the
schematic, and every pad gets the net the schematic gives its pin. Tracks
and vias on a net the schematic no longer has are deleted. New parts are
parked in a row below the board for placement by hand.

Run from the project root with KiCad's Python: python3 tools/pcb_sync.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "pico-step.kicad_pcb"
SCH = ROOT / "pico-step.kicad_sch"
STOCK_FP_DIR = Path("/usr/share/kicad/footprints")
PARK = (80.0, 130.0)


def sexpr(text: str) -> list:
    """Nested lists of atoms; quoted strings come back unquoted."""
    stack: list[list] = [[]]
    for tok in re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text):
        if tok == "(":
            stack.append([])
        elif tok == ")":
            done = stack.pop()
            stack[-1].append(done)
        elif tok.startswith('"'):
            stack[-1].append(re.sub(r"\\(.)", r"\1", tok[1:-1]))
        else:
            stack[-1].append(tok)
    return stack[0][0]


def children(node: list, name: str) -> list[list]:
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == name]


def atom(node: list, name: str) -> str:
    found = children(node, name)
    return found[0][1] if found and len(found[0]) > 1 else ""


def netlist() -> tuple[dict[str, dict], dict[tuple[str, str], str]]:
    # The s-expression netlist keeps KiCad's escapes ("{slash}" in generated
    # net names); the XML one unescapes them, and pads given those names no
    # longer match the schematic.
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "net.net"
        subprocess.run(
            ["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr",
             "-o", str(out), str(SCH)],
            check=True, capture_output=True,
        )
        tree = sexpr(out.read_text())
    comps = {}
    for c in children(children(tree, "components")[0], "comp"):
        fields = {}
        for fs in children(c, "fields"):
            for f in children(fs, "field"):
                if len(f) > 2 and f[2]:
                    fields[atom(f, "name")] = f[2]
        comps[atom(c, "ref")] = {
            "value": atom(c, "value"),
            "footprint": atom(c, "footprint"),
            "path": atom(children(c, "sheetpath")[0], "tstamps") + atom(c, "tstamps"),
            "fields": {k: v for k, v in fields.items()
                       if k not in ("Footprint", "Datasheet", "Description")},
        }
    pins = {}
    for net in children(children(tree, "nets")[0], "net"):
        for n in children(net, "node"):
            pins[(atom(n, "ref"), atom(n, "pin"))] = atom(net, "name")
    return comps, pins


def lib_path(nickname: str) -> str:
    table = (ROOT / "fp-lib-table").read_text()
    m = re.search(r'\(name "?' + re.escape(nickname) + r'"?\)\s*\(type [^)]*\)\s*\(uri "?([^")]+)"?\)', table)
    if m:
        return m.group(1).replace("${KIPRJMOD}", str(ROOT))
    return str(STOCK_FP_DIR / f"{nickname}.pretty")


def load_footprint(fpid: str) -> pcbnew.FOOTPRINT:
    lib, name = fpid.split(":", 1)
    # pcbnew.FootprintLoad goes through a plugin lookup that KiCad 10's
    # bindings return as an uncast SwigPyObject; the plugin class works.
    fp = pcbnew.PCB_IO_KICAD_SEXPR().FootprintLoad(lib_path(lib), name)
    if fp is None:
        sys.exit(f"footprint {fpid} not found")
    fp.SetFPIDAsString(fpid)
    return fp


def main() -> int:
    comps, pins = netlist()
    board = pcbnew.LoadBoard(str(BOARD))

    # Every BOARD.Remove() waits until the end: in KiCad 10's bindings, once
    # one has run, footprint loads and BOARD.GetFootprints() come back as
    # uncast SwigPyObjects.
    existing = list(board.GetFootprints())
    current = {fp.GetReference(): fp.GetFPIDAsString() for fp in existing}
    loaded = {ref: load_footprint(c["footprint"]) for ref, c in comps.items()
              if current.get(ref) != c["footprint"]}
    doomed = []
    placed = {}
    for fp in existing:
        ref = fp.GetReference()
        if ref in comps:
            placed[ref] = fp
        else:
            print(f"delete {ref} ({fp.GetFPIDAsString()})")
            doomed.append(fp)

    final = {}
    parked = 0
    for ref, c in sorted(comps.items()):
        old = placed.get(ref)
        if ref not in loaded:
            fp = old
        else:
            fp = loaded[ref]
            fp.SetReference(ref)
            board.Add(fp)
            if old is not None:
                print(f"swap {ref}: {old.GetFPIDAsString()} -> {c['footprint']}")
                if old.IsFlipped():
                    fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
                fp.SetOrientation(old.GetOrientation())
                fp.SetPosition(old.GetPosition())
                fp.SetLocked(old.IsLocked())
                doomed.append(old)
            else:
                x, y = PARK[0] + 4.0 * parked, PARK[1]
                parked += 1
                fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
                print(f"add {ref} ({c['footprint']}) parked at {x:g}, {y:g}")
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH(c["path"]))
        for name, value in c["fields"].items():
            fp.SetField(name, value)
        final[ref] = fp

    nets = {}
    for name in sorted(set(pins.values())):
        net = board.FindNet(name)
        if net is None:
            net = pcbnew.NETINFO_ITEM(board, name)
            board.Add(net)
        nets[name] = net
    for ref, fp in final.items():
        for pad in fp.Pads():
            name = pins.get((ref, pad.GetNumber()))
            if name is None:
                pad.SetNetCode(0)
            else:
                pad.SetNet(nets[name])

    alive = set(pins.values())
    for t in board.GetTracks():
        if t.GetNetCode() and t.GetNetname() not in alive:
            print(f"delete {t.GetClass()} on {t.GetNetname()}")
            doomed.append(t)
    for z in board.Zones():
        if z.GetNetCode() and z.GetNetname() not in alive:
            print(f"zone on {z.GetNetname()} has no net in the schematic, left as is")

    for item in doomed:
        board.Remove(item)
    pcbnew.SaveBoard(str(BOARD), board)
    print(f"{len(comps)} footprints, {len(alive)} nets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
