"""The schematic build: which files it copies, and its refusal to
overwrite a schematic edited in KiCad.

tools/tsch_sch.py copies each board's schematic, built from its tsch/,
over the board folder's .kicad_sch files. A file KiCad has saved since
then carries an edit that the copy would silently drop, so it must be
reported instead.
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
    (root / "b").mkdir(parents=True)
    (build / "b").mkdir(parents=True)
    monkeypatch.setattr(tsch_sch, "ROOT", root)
    monkeypatch.setattr(tsch_sch, "BUILD", build)
    (build / "b" / "a.kicad_sch").write_text(sch("tsch", "new"))
    return root / "b", build / "b"


def manifest(root: Path, board: str, sheets: list[str]) -> None:
    (root / board / "tsch").mkdir(parents=True)
    listed = ", ".join(f'"{s}"' for s in sheets)
    (root / board / "tsch" / "project.toml").write_text(
        f'name = "x-{board}"\nsheets = [{listed}]\n')


def test_generator_is_read_from_the_header(tmp_path):
    path = tmp_path / "x.kicad_sch"
    path.write_text(sch("eeschema"))
    assert tsch_sch.generator(path) == "eeschema"


def test_missing_target_is_free_to_write(dirs):
    assert not tsch_sch.saved_by_kicad("b", "a.kicad_sch")


def test_previous_tsch_build_is_overwritten(dirs):
    board, _ = dirs
    (board / "a.kicad_sch").write_text(sch("tsch", "old"))
    assert not tsch_sch.saved_by_kicad("b", "a.kicad_sch")


def test_file_saved_by_kicad_is_kept(dirs):
    board, _ = dirs
    (board / "a.kicad_sch").write_text(sch("eeschema", "moved a part"))
    assert tsch_sch.saved_by_kicad("b", "a.kicad_sch")


def test_symbol_library_is_always_copied(dirs):
    board, build = dirs
    (build / "tsch.kicad_sym").write_text("(kicad_symbol_lib)")
    (board / "tsch.kicad_sym").write_text("(kicad_symbol_lib old)")
    assert not tsch_sch.saved_by_kicad("b", "tsch.kicad_sym")


def test_boards_are_the_folders_with_a_tsch_project(tmp_path, monkeypatch):
    monkeypatch.setattr(tsch_sch, "ROOT", tmp_path)
    manifest(tmp_path, "mcu", ["mcu.tsch"])
    manifest(tmp_path, "driver", ["driver.tsch"])
    (tmp_path / "lib").mkdir()
    assert tsch_sch.boards() == ["driver", "mcu"]


def test_outputs_name_each_sheet_and_the_library(tmp_path, monkeypatch):
    monkeypatch.setattr(tsch_sch, "ROOT", tmp_path)
    manifest(tmp_path, "mcu", ["usb.tsch", "mcu.tsch", "../../stack/stack.tsch"])
    assert tsch_sch.outputs("mcu") == [
        "x-mcu.kicad_sch", "usb.kicad_sch", "mcu.kicad_sch", "stack.kicad_sch",
        "tsch.kicad_sym"]


def test_one_sheet_project_is_its_own_root(tmp_path, monkeypatch):
    # tsch writes a one-sheet project as the root sheet alone.
    monkeypatch.setattr(tsch_sch, "ROOT", tmp_path)
    manifest(tmp_path, "enc", ["enc.tsch"])
    assert tsch_sch.outputs("enc") == ["x-enc.kicad_sch", "tsch.kicad_sym"]
