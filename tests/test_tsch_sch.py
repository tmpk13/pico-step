"""The schematic build refuses to overwrite a schematic edited in KiCad.

tools/tsch_sch.py copies the schematic built from tsch/ over the project's
.kicad_sch files. A file KiCad has saved since then carries an edit that
the copy would silently drop, so it must be reported instead.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import tsch_sch  # noqa: E402


def sch(generator: str, body: str = "") -> str:
    return f'(kicad_sch\n\t(version 20260306)\n\t(generator "{generator}")\n{body})\n'


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    root, build = tmp_path / "root", tmp_path / "build"
    root.mkdir()
    build.mkdir()
    monkeypatch.setattr(tsch_sch, "ROOT", root)
    monkeypatch.setattr(tsch_sch, "BUILD", build)
    (build / "a.kicad_sch").write_text(sch("tsch", "new"))
    return root, build


def test_generator_is_read_from_the_header(tmp_path):
    path = tmp_path / "x.kicad_sch"
    path.write_text(sch("eeschema"))
    assert tsch_sch.generator(path) == "eeschema"


def test_missing_target_is_free_to_write(dirs):
    assert not tsch_sch.saved_by_kicad("a.kicad_sch")


def test_previous_tsch_build_is_overwritten(dirs):
    root, _ = dirs
    (root / "a.kicad_sch").write_text(sch("tsch", "old"))
    assert not tsch_sch.saved_by_kicad("a.kicad_sch")


def test_file_saved_by_kicad_is_kept(dirs):
    root, _ = dirs
    (root / "a.kicad_sch").write_text(sch("eeschema", "moved a part"))
    assert tsch_sch.saved_by_kicad("a.kicad_sch")


def test_symbol_library_is_always_copied(dirs):
    root, build = dirs
    (build / "tsch.kicad_sym").write_text("(kicad_symbol_lib)")
    (root / "tsch.kicad_sym").write_text("(kicad_symbol_lib old)")
    assert not tsch_sch.saved_by_kicad("tsch.kicad_sym")
