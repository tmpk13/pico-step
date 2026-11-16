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
- The stack headers, J5 and J6 (see Stack headers), are on every board,
  drawn once in `stack/stack.tsch`, which each board's project lists as a
  sheet. The same pinout on every board lets the boards stack in any order
  and keeps one home for the pinout. Their pins pass through each board,
  so a board leaves the lines it does not use unwired.
- tsch therefore warns W182 (global label appears once) on the encoder
  board for the 10 TMC lines and VM_SENSE, and on the driver board for the
  4 encoder SSC lines and TMC_DIAG0/1. These are the expected unused bus
  lines; a W182 for any other name is a real missing connection.
- Each board is its own KiCad project, so a label of the same name on two
  boards is two nets until both reach a stack header; neither tsch nor ERC
  sees across projects. `tests/test_stack.py` checks it.
- References stay unique across the stack (J5 and J6 excepted), so one
  order list serves all three boards.
- A board's `.kicad_pro` is a copy of the one-board project with its
  `meta.filename`, `schematic.top_level_sheets` and `sheets` pointed at
  the board's root sheet: KiCad 10 opens the root sheet that
  `top_level_sheets` names.
- The board-against-schematic tests (`test_board.py`, the board half of
  `test_refs.py`) skip a board while its `.kicad_pcb` is byte-identical to
  `pico-step.kicad_pcb`, and run as soon as it is edited.

## Stack headers (2026-11-15)
Two 2x06 2.54 mm headers replaced the 2x12 J5. J5 sits at the top edge
and J6 at the bottom edge, both at 90 degrees with pin 1 on the left, so
J5's odd row and J6's even row face the board center. Every board keeps
that position and rotation; `tests/test_stack.py` checks both on every
board that is no longer an uncut copy.

The driver board sets the pinout. U5 sits at 180 degrees so its VS and
OUT side faces left; that puts SLEEPN, CSN, SCK, SDI and SDO (pins 33-37)
on its bottom edge toward J6, REFL and REFR (1-2) at the lower right,
IFC, IFB, IFA and ENN (8-11) at the upper right, and DIAG0 and DIAG1
(13-14) on the top edge toward J5. So J6 carries the TMC SPI, SLEEPN,
REFL, REFR and VM_SENSE (its divider sits at the lower left), and J5 the
rest. The first split, made in the GUI by halving the old pinout, had the
TMC SPI on J5, which would loop every SPI line around U5.

- Signals take the inner row and GND the outer row where they can. An
  outer-row signal reaches its pin through the gap between two inner pins
  (0.84 mm between 1.7 mm pads, room for one trace).
- Each group sits in the order its chip's pins leave, so the fan-out
  needs no crossing. Read from the board center (inner pins and the gaps
  between them, left to right), J6 gives VM_SENSE, SLEEPN, CSN, SCK, SDI,
  SDO, REFL, REFR, and J5 gives ENC_SCK, ENC_TX, ENC_DATA, ENC_CSQ, +3V3,
  DIAG1, DIAG0, ENN, IFA, IFB, IFC.
- Each SPI clock has GND directly behind it (J5.2, J6.5); REFL and REFR
  (step and direction) have GND behind them too. VM_SENSE sits at J6's
  end beside the static SLEEPN, with GND behind it.
- Five GND pins and one +3V3 (was four and two): the +3V3 load across the
  stack is the TLE5012B and the TMC5241 logic, tens of mA. J5 has a single
  GND because its 10 signals leave no spare pin; moving R14 (ENC_TX into
  ENC_DATA) to the mcu board would drop ENC_TX from the stack and free one.
- ENC_SCK, ENC_TX, ENC_DATA, ENC_CSQ follow the RP2354A's SPI1 pins
  GPIO10-13 in order. J6 matches U1's pins 2-10 in order once TMC_SLEEPN
  moves to GPIO0 and TMC_CSN to GPIO1 (an SPI0 CSn pin); both are free
  (TODO.md). The mcu board is not placed yet, so the other MCU lines get
  their GPIOs when U1 is.

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
