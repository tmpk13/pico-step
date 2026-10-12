# TODO

- [ ] PCB: check the RP2354A core regulator against RP2350 data sheet
      Figure 26. L1, C11, C12, R27, C17 sit right of U1 on the back; still
      to do: cut the GND pour under L1 and the LX trace, separate GND vias
      for CIN and the R27/C17 filter, shorten the autorouted LX trace.
- [ ] PCB power stage review: C33/C34 are on the back under R15 and left of
      the FET row (not tight at the bridges), SRAL/SRBL return through the
      GND plane (NOTES.md, PCB floor plan), gate and BM traces are
      autorouted. Check BM undershoot stays above -5 V (data sheet 3.4).
- [ ] Decide VM overvoltage handling for regenerative braking at 48 V (no
      clamp fitted; a TVS standing off 48 V clamps above the 60 V maximum).
- [ ] PCB: the S1 to D2 link is a 0.5 mm trace around the package, not a
      wide pour (NOTES.md). Consider a wider link or a second one on the
      back, and more copper under the paddles for heat (85 C/W assumes
      1 in^2).
- [ ] Firmware: SHORT_CONF S2VS_LEVEL >= 9 and S2G_LEVEL >= 8 before
      enabling the driver (NOTES.md, short detection), and IHOLD below
      IRUN so standstill heat stays under the 0.7 W worst case.
- [ ] Check stock for the resistors not searched (DIGIKEY.md).
- [ ] Settle the hand edits that differ from `tools/circuit.py`
      (`mise run parity`): VM split from J2/C19/R12 ("Power?" note) and
      TMC5160 DIAG0/DIAG1 not wired to MCU GPIO9/GPIO17 ("Selectable?"
      note; their global labels at U1 are unconnected). Then update one or
      the other.
- [ ] PCB routing: close the connections freerouting left open (listed in
      build/drc.json after `mise run pcb-drc-json`; NOTES.md, Routing
      result), or move to a 4-layer stackup and reroute. Then clean up the
      autorouted detours (RUN, SWDIO, USB pair), check the remaining
      starved thermal reliefs and silk overlaps, and remove stitching vias
      that landed in awkward spots.
- [ ] PCB: the J2/C19 net is still split from VM (one short link from
      C19's + pad to the VM pour's left arm once the schematic decides).
