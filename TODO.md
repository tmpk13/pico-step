# TODO

- [ ] TMC2240 footprint exposed pad: confirm T3255-5 EP size against Maxim
      outline 21-0140 / land pattern 90-0013 (not in the TMC2240 data sheet;
      `ref/` has only the data sheet). Footprint currently copies T3255-3
      (EP 3.1 x 3.1 mm); update `STOCK_COPIES` in `tools/footprints.py`.
- [ ] PCB: TLE5012B on the motor shaft axis, diametric magnet; TMC2240 EP
      with many GND vias, VS caps at the VS pins.
- [ ] PCB: "Update PCB from Schematic" for the swap back to the RP2040
      (ESP32-C5, RF section, FL1_rf, J5_rf and the 48 MHz crystal leave;
      RP2040 QFN-56, W25Q128 U4, 12 MHz Y1 and R14 arrive). Placement was done
      on the ESP32-C5 netlist; refs C3..C28, R3..R8, L1..L4 changed meaning.
      `tests/test_refs.py` fails until the board matches.
- [ ] Check stock for the four passives new to the RP2040 list (DIGIKEY.md).
- [ ] Settle the hand edits that differ from `tools/circuit.py`
      (`mise run parity`): VM split from J2/C19/R12 ("Power?" note) and
      TMC2240 DIAG0/DIAG1 not wired to RP2040 GPIO12/GPIO28 ("Selectable?"
      note; their global labels at U1 are unconnected). Then update one or the other.
