#!/usr/bin/env python3
"""Build the project schematic from the text drawing in tsch/.

tsch, the text-schematic tool (TSCH names its binary, default "tsch"),
builds tsch/project.toml into build/tsch and proves the result with
kicad-cli: KiCad's netlist equals the drawn one, ERC has no errors and
every text sits in the cells it was typed in. The root sheet, the sheets
and the generated symbol library are then copied into the project root,
where pico-step.kicad_pro and the board expect them. tsch's own
.kicad_pro and sym-lib-table stay in build/tsch: the project's copies
hold the design rules, net classes and ERC settings.

A schematic file that KiCad has saved since it was generated is not
overwritten, because an edit made in the GUI is lost on the next build;
it belongs in tsch/. --force overwrites it anyway.

Run from the project root: python3 tools/tsch_sch.py [--force]
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
PROJECT = ROOT / "tsch" / "project.toml"
BUILD = ROOT / "build" / "tsch"
LIBRARY = "tsch.kicad_sym"


def outputs() -> list[str]:
    """Files to copy: root sheet, one schematic per drawn sheet, symbols."""
    project = tomllib.loads(PROJECT.read_text())
    sheets = [Path(s).with_suffix(".kicad_sch").name for s in project["sheets"]]
    return [f"{project['name']}.kicad_sch", *sheets, LIBRARY]


def generator(path: Path) -> str:
    """The program that last wrote a .kicad_sch ("tsch", "eeschema", ...)."""
    m = re.search(r'\(generator "([^"]*)"\)', path.read_text()[:1000])
    return m.group(1) if m else ""


def saved_by_kicad(name: str) -> bool:
    """True when copying NAME would overwrite a schematic edited in KiCad."""
    target = ROOT / name
    return (name.endswith(".kicad_sch") and target.exists()
            and generator(target) != "tsch"
            and target.read_bytes() != (BUILD / name).read_bytes())


def main(argv: list[str]) -> int:
    tsch = os.environ.get("TSCH", "tsch")
    subprocess.run([tsch, "verify", str(PROJECT), "-o", str(BUILD)], check=True)
    names = outputs()
    edited = [n for n in names if saved_by_kicad(n)]
    if edited and "--force" not in argv:
        print(f"not overwriting {', '.join(edited)}: saved by KiCad since it was "
              "generated. Move the change into tsch/, or pass --force to drop it.")
        return 1
    for name in names:
        shutil.copyfile(BUILD / name, ROOT / name)
    print(f"copied {', '.join(names)} from {BUILD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
