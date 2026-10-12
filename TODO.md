# TODO

- [ ] PCB: "Update PCB from Schematic" for the RP2040 swap-back and the
      TMC5160A driver (ESP32-C5, RF section, FL1_rf, J5_rf, 48 MHz crystal
      and the TMC2240 leave; RP2040, W25Q128 U4, 12 MHz Y1, R14, U5
      TMC5160A, Q1..Q8, C27..C35 and R18..R26 arrive). Refs C3..C28,
      R3..R8, R15..R17, L1..L4 changed meaning. `tests/test_refs.py` fails
      until the board matches.
- [ ] PCB: TLE5012B on the motor shaft axis, diametric magnet.
- [ ] PCB power stage: FETs and C33/C34 tight around each half bridge, R15/R18
      Kelvin traces to SRAL/SRBL, short gate and BM traces, C21/C23 at the
      VS/VCP pins, C27 to GNDA, many vias under the U5 exposed pad. Check
      BM undershoot stays above -5 V (data sheet section 3.4).
- [ ] Decide VM overvoltage handling for regenerative braking at 48 V (no
      clamp fitted; a TVS standing off 48 V clamps above the 60 V maximum).
- [ ] Confirm the motor current target. RSENSE 0.1 gives 2.3 A RMS full
      scale; more needs lower RSENSE and a connector rated above 3 A.
- [ ] Check stock for the resistors not searched (DIGIKEY.md).
- [ ] Settle the hand edits that differ from `tools/circuit.py`
      (`mise run parity`): VM split from J2/C19/R12 ("Power?" note) and
      TMC5160 DIAG0/DIAG1 not wired to RP2040 GPIO9/GPIO17 ("Selectable?"
      note; their global labels at U1 are unconnected). Then update one or
      the other.
