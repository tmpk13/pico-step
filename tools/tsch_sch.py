#!/usr/bin/env python3
"""Build each board's schematic from its text drawing in <board>/tsch/.

The project is a stack of boards; every board folder holding
tsch/project.toml is one. tsch, the text-schematic tool (TSCH names its
binary, default "tsch"), builds a board's project.toml into
build/tsch/<board> and proves the result with kicad-cli: KiCad's netlist
equals the drawn one, ERC has no errors and every text sits in the cells
it was typed in. The root sheet, the sheets and the generated symbol
library are then copied into the board folder, where its .kicad_pro and
board expect them. tsch's own .kicad_pro and sym-lib-table stay in the
build folder: the board's copies hold the design rules, net classes and
ERC settings.

A schematic file that KiCad has saved since it was generated is not
overwritten, because an edit made in the GUI is lost on the next build;
it belongs in the board's tsch/. --force overwrites it anyway.

Run from the project root: python3 tools/tsch_sch.py [BOARD ...] [--force]
(no BOARD builds every board).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build" / "tsch"
LIBRARY = "tsch.kicad_sym"


def boards() -> list[str]:
    """Board folder names: every top-level folder with tsch/project.toml."""
    return sorted(p.parent.parent.name for p in ROOT.glob("*/tsch/project.toml"))


def project(board: str) -> Path:
    return ROOT / board / "tsch" / "project.toml"


def outputs(board: str) -> list[str]:
    """Files to copy: root sheet, one schematic per drawn sheet, symbols.

    A one-sheet project has no separate sheet file: the drawing is the
    root sheet itself.
    """
    manifest = tomllib.loads(project(board).read_text())
    root = f"{manifest['name']}.kicad_sch"
    if len(manifest["sheets"]) == 1:
        return [root, LIBRARY]
    sheets = [Path(s).with_suffix(".kicad_sch").name for s in manifest["sheets"]]
    return [root, *sheets, LIBRARY]


def generator(path: Path) -> str:
    """The program that last wrote a .kicad_sch ("tsch", "eeschema", ...)."""
    m = re.search(r'\(generator "([^"]*)"\)', path.read_text()[:1000])
    return m.group(1) if m else ""


def saved_by_kicad(board: str, name: str) -> bool:
    """True when copying NAME would overwrite a schematic edited in KiCad."""
    target = ROOT / board / name
    return (name.endswith(".kicad_sch") and target.exists()
            and generator(target) != "tsch"
            and target.read_bytes() != (BUILD / board / name).read_bytes())


def main(argv: list[str]) -> int:
    tsch = os.environ.get("TSCH", "tsch")
    known = boards()
    chosen = [a for a in argv if not a.startswith("--")] or known
    unknown = [b for b in chosen if b not in known]
    if unknown:
        print(f"no board {', '.join(unknown)}; boards: {', '.join(known)}")
        return 1
    for board in chosen:
        subprocess.run([tsch, "verify", str(project(board)), "-o", str(BUILD / board)],
                       check=True)
    edited = [f"{b}/{n}" for b in chosen for n in outputs(b) if saved_by_kicad(b, n)]
    if edited and "--force" not in argv:
        print(f"not overwriting {', '.join(edited)}: saved by KiCad since it was "
              "generated. Move the change into the board's tsch/, or pass --force "
              "to drop it.")
        return 1
    for board in chosen:
        names = outputs(board)
        for name in names:
            shutil.copyfile(BUILD / board / name, ROOT / board / name)
        print(f"{board}: copied {', '.join(names)} from "
              f"{(BUILD / board).relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
