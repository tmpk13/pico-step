# Schematic

## Hand-placed schematic
The schematic was arranged in the KiCad GUI after generation, including
connectivity edits (VM split from J2, DIAG0/DIAG1 not wired to the MCU,
R16/R17 swapped). Regenerating it from circuit.py erased all of that once,
so `mise run sch` now writes `build/pico-step.gen.kicad_sch` only.
The RP2040 swap-back was done in place: ESP32-only parts were removed by
wire cluster (pin positions computed from lib_symbols, every wire end checked
to land on a pin, wire or label), wires from U5/J1/VM_SENSE to the old MCU
were cut back to global-label stubs, and the RP2040 block was laid out alone
with kicad-vis and pasted below the existing parts. Paste details: rewrite
symbol instances to this project's root sheet path, renumber #PWR, drop the
block's PWR_FLAGs (they clash with the AP2112K output), and keep one power
symbol per stacked supply pin (IOVDD x6, DVDD x2). TLE5012B labels at R9/R11
were renamed SPI_SCK -> ENC_SCK and SPI_MOSI -> ENC_DATA for the RP2040
SPI1 wiring.

The TMC2240 -> TMC5160A swap was done the same way: 107 items of the old
driver block removed by cluster, the three ENC_IFx wires to U3 cut back to
global-label stubs at U3, the new block laid out alone with kicad-vis and
pasted at (465, 88) mm. The sheet went from A2 to A1 so nothing existing had
to move. Paste details that differ from the RP2040 paste: kicad-vis draws a
net that crosses the block boundary as a local label, and a boundary net
with two pins inside the block (TMC_ENN: U5 and its pull-up) as a bare wire
with no label at all, which would silently cut it from the MCU. Boundary
labels were converted to global labels and TMC_ENN got one. kicad-vis also
places a symbol's Reference/Value itself, over U5's top and bottom pin
numbers, so they were moved outside the body corners after the paste. The
hand edits survive: DIAG0/DIAG1 reach only their pull-ups ("Selectable?"
note moved next to them) and VM stays split from J2.

The RP2040 -> RP2354A swap kept U1's position and uuid (both symbols span
the same +-25.4 x +-45.72 mm). Every wire, label, power symbol and NC flag
attached to U1, U4 and C17 was removed by cluster; each new pin was then
wired with a stub and the label the old pin of the same name had, so the
hand edits (DIAG0/DIAG1 labels at U1 left floating) carry over. R14.1 and
R5.1 had wires straight to the old U1 and got labels instead. The regulator
parts sit where U4 was.

The TMC5160A -> TMC5241 swap followed the same recipe: 63 symbols, 125
wires and 88 labels of the old block removed by cluster (no cluster mixed
old and kept parts), the new block laid out alone with kicad-vis and
pasted over the same area (offset 439.42, 58.42 mm). Boundary labels went
global; TMC_ENN and TMC_SLEEPN came out as bare wires again (two pins in
the block) and got global labels at R24 and R25. kicad-vis also left the
motor outputs, CPI and IREF unlabeled, so they became Net-(J4-Pin_1) and
the like, which the power net class pattern `/OUT*` does not match; local
labels at U5 put the names back. The MCU side labels were renamed
(TMC_REFL, TMC_REFR, TMC_SLEEPN). DIAG0/DIAG1 still reach only their
pull-ups, and the "Selectable?" note sits beside them.

## DigiKey list
- eparts-search returns the reel (TR) variant of most passives; use the MPN in
  the DigiKey list upload so packaging can be chosen there.
- Two first-choice Murata MPNs were obsolete (100n 50V 0603, 10u 0805);
  alternates are in DIGIKEY.md.
- `tests/test_refs.py` checks that the order list names every generator
  reference exactly once and that quantities add up.

## Text drawing (tsch/)
`tsch/` draws the hand schematic again as text for `tsch`, the
text-schematic tool (one character is one 1.27 x 2.54 mm cell; `tsch spec`
prints the format). It is an experiment beside the hand schematic, which
stays the source for `pcb-sync`. `mise run tsch-parity` proves the two
equal: all 54 multi-pin nets match pin for pin. The one intended part
difference is C11/C12, drawn at 4.7u where the hand schematic still reads
1u (see TODO).

- Four sheets (power, mcu, encoder, driver) joined by global labels and
  power ports. The RP2354A is two units: U1A holds the supply pins and the
  core regulator, U1B the IO.
- tsch draws a horizontal two-pin part with pin 1 on the left, so L1, R5
  and R8 are drawn vertical (pin 1 on top) to keep the hand schematic's pin
  numbering. L1's pin 1 is the polarity dot and must stay on +1V1.
- tsch has no label in the middle of a wire, so a directly wired net stays
  unnamed. The motor outputs carry local labels at both U5 and J4. In the
  multi-sheet build they are named `/driver/OUT1A`, and the charge pump
  nets `Net-(U5-VCP)` and the like, so the board's net class patterns
  (`/OUT*`, `/TMC_VCP`, `/TMC_CPI`, `/TMC_CPO`) would need new patterns
  before this drawing could drive the board.
- Switches and the crystal are plain boxes; tsch has no glyph for them.
- The build directory has no `pico-step` footprint library, so ERC there
  warns `footprint_link_issues` for J1, U3, L1 and U5; it does not affect
  the netlist.
