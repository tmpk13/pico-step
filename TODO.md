# TODO

- [ ] PCB: check the RP2354A core regulator against RP2350 data sheet
      Figure 26. L1, C11, C12, R27, C17 sit right of U1 on the back; still
      to do: cut the GND pour under L1 and the LX trace, separate GND vias
      for CIN and the R27/C17 filter, shorten the autorouted LX trace.
- [ ] PCB: place the TMC5241 stage like the TMC5241-EVKIT (notes/driver.md):
      C21/C33 at the pin 30 end and C22/C34 at the pin 21 end of the VS/OUT
      row, 25/26 joined to them (on the back, outside the EP GND, or
      between the OUT2B/OUT2A traces), C23/C24 under pins 16..18, R15/C25
      at pins 3/5, J4 beside the OUT pins, GND copper and vias under the EP
      on both sides. U5, R15, C25 and the kept parts sit at the old
      positions.
- [ ] Decide the motor current the board can hold. 1.7 A RMS (the 48 V
      rating) is about 2.7 W in U5 when hot, too much for a two-layer
      42 mm board; about 1.2 A RMS is a safer continuous figure (notes/driver.md,
      TMC5241 at 48 V). Four layers raise it.
- [ ] Decide VM overvoltage handling for regenerative braking at 48 V (no
      clamp fitted; absolute maximum 70 V). The TMC5241 OV pin can drive a
      brake chopper MOSFET and dump resistor (data sheet Figure 39); it is
      unconnected now. The TMC5241-EVKIT fits both an SMCJ54A TVS and a
      brake output (notes/driver.md).
- [ ] Check the TQFN-38 footprint against package outline 21-0172 (only
      land pattern 90-0076 was available; analog.com timed out).
- [ ] Firmware: TMC5241 bring-up with DRV_ENN high, nSLEEP (GPIO18) high,
      2.5 ms wake, DRV_CONF current range 2 (3 A full scale with RREF 12k),
      GLOBALSCALER/IRUN for the chosen current, then DRV_ENN low. Never
      sleep or reset while the motor turns fast.
- [ ] Schematic and board: set C11 and C12 to 4.7u in the KiCad GUI, then
      `mise run pcb-sync`. They still read 1u from the RP2040 design;
      `tools/circuit.py`, BOM.md and the DigiKey list have 4.7u (RP2350
      data sheet 6.3.8, notes/circuit.md).
- [ ] Settle the hand edits that differ from `tools/circuit.py`
      (`mise run parity`): VM split from J2/C19/R12 ("Power?" note) and
      TMC5241 DIAG0/DIAG1 not wired to MCU GPIO9/GPIO17 ("Selectable?"
      note; their global labels at U1 are unconnected). Then update one or
      the other.
- [ ] PCB routing: the board has no tracks since the GUI re-placement.
      Route after placing the TMC5241 stage; a 4-layer stackup with GND
      and 3V3 planes also cools U5 (28 against 38 C/W). The freerouting
      pipeline and what helped it are in notes/pcb.md, Routing result.
- [ ] PCB: the J2/C19 net is still split from VM (one short link from
      C19's + pad to the VM pour's left arm once the schematic decides).
