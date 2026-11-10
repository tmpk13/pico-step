# PCB

## pcbnew scripting (KiCad 10.0.4)
- KiCad's `pcbnew` module exists only for the system Python; the project
  venv (mise Python 3.13) cannot import it, so the PCB tasks run
  `$KICAD_PYTHON` (`/usr/bin/python3`, set in mise.toml).
- Once `BOARD.Remove()` has run on a footprint, later footprint loads and
  `BOARD.GetFootprints()` return uncast `SwigPyObject`s. `pcb_sync.py`
  collects everything first and removes last.
- `pcbnew.FootprintLoad()` returns an uncast object as well; the plugin
  class works: `pcbnew.PCB_IO_KICAD_SEXPR().FootprintLoad(lib_dir, name)`.
- `kicad-cli sch export netlist --format kicadxml` unescapes KiCad's
  `{slash}` in generated net names (`unconnected-(U1-GPIO27{slash}ADC1-
  Pad41)`), so pads given those names fail DRC schematic parity with
  `net_conflict`. The s-expression netlist keeps the escape.

## PCB floor plan
The 42.2 mm square with 31 mm hole spacing is a NEMA17 back-mount: U3 sits
on the back at the shaft axis (100, 100). The back faces the motor, so it
only carries parts under 1.2 mm tall (U1 with its regulator, decoupling and
pull resistors, U3 and its series resistors, the USB CC and LDO parts
under J1). Keep a 6 mm radius around the center on the back free for the
shaft magnet; nothing but U3 is inside it. M3 heads need about 3 mm radius
around each hole on both sides.

The placement is a table in `tools/pcb_place.py`; re-running it
overwrites GUI moves. Since the TMC5241 swap the board is being placed
again by hand: the routing was removed in the GUI and many parts sit
outside the outline.

TMC5241 swap on the board (`mise run pcb-sync`, `tools/pcb_sync.py`): the
four FETs, both sense resistors, the sense filters, the bootstrap and
gate supply parts and R26 were deleted; U5, R15 and C25 got their new
footprints at the old positions; every pad took the schematic's net and
every footprint the new symbol's uuid, so a later "Update PCB from
Schematic" in the GUI matches by link. The stage still has to be placed,
following the TMC5241-EVKIT (see that section): C21/C33 at the pin 30
corner and C22/C34 at the pin 21 corner, the middle VS pair 25/26 joined
to them, C23 and C24 under pins 16..18, R15 and C25 next to pins 3 and 5,
J4 beside the OUT pins, and as much GND copper and via area under the EP
as the board allows (see TMC5241 at 48 V).

The TMC5160A layout (commit 9fd8961), for reference: J4 and
the two buttons on the top edge, the four dual FETs in a row under it
with the sense resistors below, U5 under those, then J2, the crystal and
J3 on the bottom edge. Each FET's S1 lead reached its D2 paddle by a
0.5 mm trace around the package, VM came from a pour on the back through
vias into the drain paddles, and the phase pairs crossed between layers
on the way to J4. `tools/pcb_route.py` (removed with the FETs) laid that
copper down locked before autorouting.

- U1 is rotated so its SPI/STEP/DIR pins (1..15) face U5's digital edge
  across a corridor kept free of top side parts; with those pins facing
  the board edge the autorouter had to loop every driver line around the
  chip and left a third of the board unrouted. The regulator pins end up
  at the top left of U1, beside (not under) U5's thermal via field, and
  the encoder, SWD and crystal pins at the bottom edge.
- The crystal is on the top at the bottom edge with two vias to U1's
  XIN/XOUT pins; next to U1 on the back it blocked the escape of the
  neighboring pins.
- Rules for the autorouter: 0.15 mm track and clearance, 0.5/0.3 mm vias
  (JLCPCB 2-layer limits). With 0.2/0.2 freerouting could not leave the
  0.4 mm pitch QFN-60 pads at all (a 0.2 mm trace centered on a 0.2 mm
  pad has exactly 0.2 mm to the neighbors, and the router needs margin),
  and it left over 120 of 142 connections unrouted.
- The Specctra export writes locked tracks as `(type fix)`, and the planes
  (GND on both layers, VM on the back) are exported as conduction areas,
  so the autorouter neither moves them nor routes GND.
- Freerouting 2.1.0 from the CLI still opens its GUI; with an empty
  profile email it then shows a modal User Settings dialog after routing
  and never writes the session file (it also opens the GUI on whatever
  DISPLAY is set, and dies with HeadlessException without one). With
  logging on it looked like a hang at "traces not 45 degree".
  `tools/freerouting_profile.py` writes a dummy email into
  /tmp/freerouting/freerouting.json, telemetry off, before each run.
- Net-(J2-Pin_1) is still split from VM (see "Power?"): J2 pin 1 is wired
  to C19 only. The link to VM is one short trace from C19's + pad to the
  VM pour's left arm once the schematic decides.

## Routing result
This is the TMC5160A board (commit 9fd8961); the TMC5241 board is not
routed yet. Pipeline then: `pcb-place`, `pcb-route` (removed),
`pcb-fill`, `pcb-dsn`, `pcb-autoroute`, `pcb-ses`, `pcb-gnd`, `pcb-drc`.
The power stage and VM distribution were hand-routed (locked);
freerouting 2.1.0 routes the signals with 0.15 mm
rules and 0.5 mm vias in about four minutes for 30 passes. Over six
placement variants it never got below about 20 open signal connections
of 142 (the committed board: 21 after 60 passes, plus 30 GND pads and
islands the stitching could not reach); its result also varies by about
10 between runs on similar inputs. The open ones cluster at U5's left edge (12VOUT, 5VOUT, CB1,
SRAH), its right edge (CPO, CPI, VCP, CA2, ENN, DIAG, ENCN), a few gate
lines where the FET lead row meets the sense resistor links, and U1's
bottom edge (encoder, SWD, crystal). `pcb-gnd` then stitches the GND
islands the dense routing leaves behind.

What helped most, in order: rules 0.15/0.15 instead of 0.2/0.2 (the
router could not leave the 0.4 mm pitch QFN pads), turning U1 so its SPI
pins face U5, 0.8 mm instead of 1.0 mm sense vias beside the gate pins,
keeping the VM feed off the back under U5's right edge, and tightening
the GND pour to 0.25 mm clearance. Removing the GND planes from the
export, or the fixed pre-routes, made it worse.

Finishing the board means closing the remaining connections in the
KiCad editor (they are listed by `mise run pcb-drc-json` in
build/drc.json under unconnected_items) or, more comfortably, going to
four layers with GND and 3V3 inner planes, which also suits a 48 V
chopper next to the MCU. The autorouted traces are freerouting quality:
functional, with detours worth cleaning up by hand (RUN and SWDIO run
along the bottom and right edges, USB D+/D- are not a tight pair).
