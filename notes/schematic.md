# Schematic

## Source: the text drawing in tsch/
The schematic is drawn as text for `tsch`, the text-schematic tool (one
character is one 1.27 x 2.54 mm cell; `tsch spec` prints the format).
`mise run sch` (tools/tsch_sch.py) builds `tsch/project.toml`, proves it
with kicad-cli (KiCad's netlist equals the drawn one, ERC clean, every text
inside its cells) and copies `pico-step.kicad_sch`, the four sheets and
`tsch.kicad_sym` into the project root. Those files are generated and
ignored by git; edit `tsch/*.tsch`.

- tsch also writes a `.kicad_pro` and `sym-lib-table` into build/tsch.
  They are not copied: the project's `.kicad_pro` holds the design rules,
  net classes and ERC severities, and the committed `sym-lib-table` points
  at the generated `tsch.kicad_sym`.
- A schematic file saved from KiCad since it was generated is not
  overwritten (its header names `eeschema`, not `tsch`), because the next
  build would drop the GUI edit without any check noticing. Move the edit
  into tsch/; `python tools/tsch_sch.py --force` discards it.
- tsch builds are byte for byte repeatable, so the board's symbol links
  (paths) stay put across rebuilds.
- ERC ignores `power_pin_not_driven`: it fires on every rail fed through a
  connector or a passive. `pin_not_driven` stays on as the signal check.

## Drawing decisions
- Four sheets (power, mcu, encoder, driver) joined by global labels and
  power ports. The RP2354A is two units: U1A holds the supply pins and the
  core regulator, U1B the IO.
- tsch draws a horizontal two-pin part with pin 1 on the left, so L1, R5
  and R8 are vertical (pin 1 on top) to keep the board's pin numbering. L1's
  pin 1 is the polarity dot and must stay on +1V1.
- tsch has no label in the middle of a wire, so a net wired directly stays
  unnamed and KiCad names it after a pin (`Net-(U5-VCP)`). Local labels on
  a sheet get the sheet path (`/driver/OUT1A`). The net class patterns in
  `pico-step.kicad_pro` follow these names: `/driver/OUT*` and `VM_IN`
  (power), `Net-(U5-VCP)`, `Net-(U5-CPI)`, `Net-(U5-CPO)` (gate). Renaming
  a pin or moving a label to another sheet silently moves its net back to
  the Default class.
- The J2 input net is the `VM_IN` power port so the power class has a
  stable name; it is not joined to `VM` yet (open decision, note on the
  power sheet). MCU GPIO9/GPIO17 carry `TMC_DIAG0`/`TMC_DIAG1` labels that
  reach nothing, as DIAG0/DIAG1 reach only their pull-ups (note on the
  driver sheet).
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
