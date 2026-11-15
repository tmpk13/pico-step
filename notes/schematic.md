# Schematic

## Source: one text drawing per board
The schematic is drawn as text for `tsch`, the text-schematic tool (one
character is one 1.27 x 2.54 mm cell; `tsch spec` prints the format).
Each board folder (mcu, encoder, driver) holds `tsch/project.toml`, whose
`name` (`pico-step-<board>`) names the board's KiCad files; every folder
with one is a board to tools/tsch_sch.py, the tests and the mise tasks.
`mise run sch` builds each, proves it with kicad-cli (KiCad's netlist
equals the drawn one, ERC clean, every text inside its cells) and copies
the root sheet, the sheets and `tsch.kicad_sym` into the board folder.
Those files are generated and ignored by git; edit `<board>/tsch/*.tsch`.

- tsch also writes a `.kicad_pro` and `sym-lib-table` into
  build/tsch/<board>. They are not copied: the board's `.kicad_pro` holds
  the design rules, net classes and ERC severities, and its committed
  `sym-lib-table` points at the generated `tsch.kicad_sym`.
- A schematic file saved from KiCad since it was generated is not
  overwritten (its header names `eeschema`, not `tsch`), because the next
  build would drop the GUI edit without any check noticing. Move the edit
  into the board's tsch/; `python tools/tsch_sch.py --force` discards it.
- tsch builds are byte for byte repeatable, so a board's symbol links
  (paths) stay put across rebuilds. The paths derive from the project
  name: renaming a board's project relinks nothing until pcb-sync runs.
- ERC ignores `power_pin_not_driven`: it fires on every rail fed through a
  connector or a passive. `pin_not_driven` stays on as the signal check.

## Stack split (2026-11-14)
The one-board schematic was split into three stacked boards; commit
2a6ebd5 has the last one-board drawing.

- The old power sheet served two boards: USB-C and the 3.3 V LDO went to
  the mcu board (`usb.tsch`), J2, C19 and the VM_SENSE divider to the
  driver board (`vm.tsch`), so 48 V never crosses the stack; VM_SENSE
  crosses already divided.
- One bus header, J5 (2x12, 2.54 mm), on every board, drawn once in
  `stack/stack.tsch`, which each board's project lists as a sheet. The
  same pinout on every board lets the boards stack in any order and keeps
  one home for the pinout. Its pins pass through each board, so a board
  leaves the lines it does not use unwired.
- tsch therefore warns W182 (global label appears once) on the encoder
  board for the 10 TMC lines and VM_SENSE, and on the driver board for the
  4 encoder SSC lines and TMC_DIAG0/1. These are the expected unused bus
  lines; a W182 for any other name is a real missing connection.
- Each board is its own KiCad project, so a label of the same name on two
  boards is two nets until both reach J5; neither tsch nor ERC sees across
  projects. `tests/test_stack.py` checks it.
- References stay unique across the stack (J5 excepted), so one order
  list serves all three boards.
- A board's `.kicad_pro` is a copy of the one-board project with its
  `meta.filename`, `schematic.top_level_sheets` and `sheets` pointed at
  the board's root sheet: KiCad 10 opens the root sheet that
  `top_level_sheets` names.
- The board-against-schematic tests (`test_board.py`, the board half of
  `test_refs.py`) skip a board while its `.kicad_pcb` is byte-identical to
  `pico-step.kicad_pcb`, and run as soon as it is edited.

## Drawing decisions
- Sheets per board: mcu (usb, mcu, stack), encoder (encoder, stack),
  driver (vm, driver, stack), joined within a board by global labels and
  power ports. The RP2354A is two units: U1A holds the supply pins and the
  core regulator, U1B the IO.
- tsch draws a horizontal two-pin part with pin 1 on the left, so L1, R5
  and R8 are vertical (pin 1 on top) to keep the board's pin numbering. L1's
  pin 1 is the polarity dot and must stay on +1V1.
- tsch has no label in the middle of a wire, so a net wired directly stays
  unnamed and KiCad names it after a pin (`Net-(U5-VCP)`). Local labels on
  a sheet get the sheet path (`/driver/OUT1A`). The net class patterns in
  every board's `.kicad_pro` follow these names: `/driver/OUT*` and `VM_IN`
  (power), `Net-(U5-VCP)`, `Net-(U5-CPI)`, `Net-(U5-CPO)` (gate). Renaming
  a pin or moving a label to another sheet silently moves its net back to
  the Default class.
- The J2 input net is the `VM_IN` power port so the power class has a
  stable name; it is not joined to `VM` yet (open decision, note on the
  vm sheet). MCU GPIO9/GPIO17 carry `TMC_DIAG0`/`TMC_DIAG1` to J5, where
  the driver board leaves them unwired, as DIAG0/DIAG1 reach only their
  pull-ups (note on the driver sheet).
- Switches and the crystal are plain boxes; tsch has no glyph for them.

## Swap from the hand-placed schematic
Until 2026-11-10 the schematic was placed by hand in KiCad, with
`tools/circuit.py` as a reference netlist. Before the swap the tsch build
matched the hand schematic on all 54 multi-pin nets, pin for pin; only C11
and C12 changed (1u to 4.7u). The last hand-placed version is commit
caadca5. `tools/circuit.py`, its kicad-vis layout and `tools/symbols.py`
were retired; their design notes live in notes/driver.md, notes/circuit.md
and on the sheets.

## DigiKey list
- eparts-search returns the reel (TR) variant of most passives; use the MPN in
  the DigiKey list upload so packaging can be chosen there.
- Two first-choice Murata MPNs were obsolete (100n 50V 0603, 10u 0805);
  alternates are in DIGIKEY.md.
- `tests/test_refs.py` checks that the order list names every schematic
  reference exactly once and that quantities add up.
