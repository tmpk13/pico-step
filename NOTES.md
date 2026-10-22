# Notes

## TLE5012B DATA line on an RP2354A SPI master
The sensor's SSC DATA pin is half duplex. The data sheet (Figure 11) wants
470R on DATA and a master whose TX tri-states. RP2350 SPI TX never
tri-states, so GPIO11 (SPI1 TX) joins the MCU-side DATA node through 4.7k
and GPIO12 (SPI1 RX) reads it directly. When the sensor drives through
470R against TX through 4.7k, the node lands within ~0.3 V of the sensor's
level, so reads are correct while TX idles at either level. Writes go
TX -> 4.7k -> 470R -> sensor input (RC well under one bit at <= 8 MHz SSC).
Single-pin PIO on GPIO12 also works; leave GPIO11 as an input then.

## TLE5012B E5000 variant
E5000 is preconfigured for PWM on IFA, but SSC stays available. IFA, IFB and
IFC all go to GPIOs so firmware can switch to IIF (A/B/index) later.

## PG-DSO-8 land pattern
Taken from the TLE5012B data sheet Figure 40 (1.31 x 0.65 mm pads, 1.27
pitch, 5.69 mm row center to center), not KiCad's IPC SOIC-8 (1.95 x 0.6).

## USB-C shield pin: S1 vs SH
kicad-vis embeds symbols from the KiCad 10.0.3 AppImage library, where the
USB-C shield is pin "SH" and the GCT USB4105 footprint pads are "SH". The
system KiCad 10.0.4 library names both "S1". Mixing the two leaves the
shield pads with no net and no check reports it. The project carries its own
footprint copy with "SH" pads, and `tests/test_footprints.py` checks that
every circuit pin exists as a pad on the named footprint and vice versa.

## Power
Logic is USB powered (VBUS -> AP2112K-3.3). Motor supply VM enters on J2,
is not tied to VBUS, and runs up to 48 V. VM_SENSE (100k/5.6k) puts 48 V at
2.55 V and reaches the 3.3 V ADC limit at 62 V, about the 63 V rating of
the bulk capacitors (the TMC5241 itself runs to 65 V). Every part on VM is
rated 63 V or more.

## TMC5241 data sheet and package
- `ref/tmc5241.pdf` is the TMC5241 data sheet rev 0 (08/25). The land
  pattern is ADI/Maxim 90-0076 rev C (`ref/90-0076.pdf`, 38L TQFN 5x7,
  package code T3857+1C). analog.com timed out for scripted downloads, so
  the outline drawing 21-0172 is not in the repo.
- The project footprint follows 90-0076: 0.25 x 0.75 mm pads, 4.88 mm
  between the 12-pad rows, 6.85 mm between the 7-pad rows, EP 3.65 x 5.60.
  KiCad's stock `WQFN-38-1EP_5x7mm_P0.5mm_EP3.65x5.65mm` is tagged
  T3857-1C but has 0.8 mm pads, rows 4.9/6.9 and a 5.65 mm EP.
  The EP has copper on both sides, 15 vias of 0.6/0.3 mm (the board's via
  rule, so no widening after placement as the TQFP-48 needed) and six
  paste windows, about 58% of the pad.
- Pin numbers from the pin table, checked against the top view: pins
  1..12 along one 7 mm side, counter clockwise. All 38 pins and the EP are
  tested. Slashes in the data sheet names (CSN/AD2, DIAG1/SW) are
  underscores in the symbol, so generated net names stay readable.
- History: the TMC5160A with four SQJB68EP dual FETs is commit 59111f8
  (last schematic) and 9fd8961 (last routed board); the TMC2240 version
  is d537741. C21..C26,
  C33..C35, R15..R17, R24, R25 and J4 kept their numbers; C23 (1u VCP),
  C25 (2.2u VDD1V8), R15 (12k RREF) and R25 (nSLEEP pull-down) are
  different parts or roles now.

## TMC5241 at 48 V
- VS 4.5..65 V, absolute maximum 70 V (TMC5160A: 55/60 V). 2 A RMS per
  coil at 24 V, 1.7 A RMS at 48 V. RDS(on) high + low side 0.31 Ohm
  typical, about 50% more when hot.
- Full scale: R15 = 12k (the smallest allowed) gives 2.05 A RMS with
  DRV_CONF current range 2 or 3 (KIFS 36 A x kOhm, Table 17). The
  power-on range 0 gives 0.67 A RMS. GLOBALSCALER brings it down to the
  current the board can take. Overcurrent trips at 5 A minimum in the
  3 A range.
- Heat: about 2 x I^2 x RDS(on) for the two bridges, conduction only.
  1.7 A RMS: 1.8 W cold, 2.7 W hot. 1.2 A RMS: 0.9 W cold, 1.3 W hot.
  Theta JA is 28 C/W on a four-layer JEDEC board and 38 C/W on one layer,
  so this two-layer 42 mm board runs about 50 C over ambient at 1.2 A and
  far too hot at 1.7 A continuous. The data sheet calls the thermal design
  critical above 24 V or 1.5 A RMS. The TMC5160A version was capped at
  1.6 A by FET heat.
- Charge pump: the CPI-CPO capacitor swings over the whole supply (CPO
  reaches VS + 2.7 V, 51 V at 48 V), so it is 22n 100V where the data
  sheet says 50 V. VCP-VS sees only about 2.7 V (1u 25V).
- No overvoltage clamp. The OV pin is the hook for one: open drain,
  released while the internal ADC reads VS >= OVERVOLTAGE_VTH (VS =
  ADC_VSUPPLY x 17.6 mV), chopping at 3-4 kHz. Figure 39 drives a logic
  level MOSFET with a dump resistor to VS from OV with a 24k pull-up to
  5 V. Not fitted, OV is unconnected. OV floats in sleep, so that pull-up
  would switch the brake on while the driver sleeps.

## TMC5241 pin strapping
- UART_EN (12) and CLK (38) to GND: SPI, internal clock. AIN (4) to GND,
  unused. The N.C. pins 19, 20, 31, 32 go to GND for cooling, which the
  pin table allows. EP is GND.
- There is no STEP/DIR input and no SD_MODE: the ramp generator always
  runs. REFL/REFR (1, 2) are reference switch inputs, still on GPIO6/GPIO7
  (labels TMC_STEP/TMC_DIR renamed TMC_REFL/TMC_REFR), so firmware can
  stop the ramp from the angle sensor. DIAG0/DIAG1 can output STEP/DIR
  for an external driver.
- nSLEEP (33) on GPIO18 (the old SD_MODE) with R25 10k to GND. Low is
  sleep: supplies off, every register cleared, bridges off, under 25 uA
  from VS. A low pulse over 30 us is a reset; wake takes 2.5 ms. The pin
  is VS rated with a 0.9 V threshold and an internal pull-down of 0.8 MOhm
  minimum. Do not sleep or reset at speed (the motor feeds energy back).
  Bring-up: DRV_ENN high, nSLEEP high, configure, then DRV_ENN low.
  ```mermaid
  gantt
      title TMC5241 bring-up (ms)
      dateFormat x
      axisFormat %L
      section nSLEEP GPIO18
      low, asleep (R25)          :0, 1
      high                       :1, 9
      section TMC5241
      waking, 2.5 ms             :1, 4
      SPI configuration          :4, 7
      section DRV_ENN GPIO8
      high, bridges off (R24)    :0, 7
      low, bridges on            :7, 9
  ```
- DRV_ENN (11) now has an internal pull-up, 60..140k. Against the MCU's
  ~50k reset pull-down that settles anywhere from 1.1 to 2.4 V, so R24 10k
  to 3V3 stays (2.75 V, above VIH = 2.31 V).
- ENCA/ENCB/ENCN (10, 9, 8) are inputs with pull-ups. The 1k in series
  with ENCN (R26) guarded against the TMC5160A's ENCN_DCO output and is
  gone.
- DIAG0/DIAG1 keep 10k pull-ups (4.7k..100k in open drain mode). DIAG0 is
  held low while the IC is in reset.

## MCU choice
The board went RP2040 -> ESP32-C5HF4 -> RP2040 -> RP2354A. The ESP32-C5 version
(dual-band Wi-Fi, RF diplexer, TLE5012B on a shared 3-wire SPI bus, strap
rules) is commit eee3e1e plus 1840e9d; 738db68 holds its schematic and PCB
placement. Swapping back restored the generator, symbols, footprints and
tests from b46301c. The PCB still carries the ESP32 footprints and needs
Update PCB from Schematic; the shared references (C3.., R3.., Y1) mean
different parts now, so check the placement of every reused reference.

## RP2354A
- RP2350A die with 2 MB flash stacked in the package, so U4 (W25Q128) and
  its decoupling are gone. The in-package flash sits on the QSPI bus; the
  QSPI_SCLK/SD0..SD3 pins stay bonded out and are left open (they can carry
  a second QSPI device with GPIO0 as XIP_CS1n). QSPI_SS still keeps the
  BOOTSEL button through 1k: the boot ROM samples it.
- Pinout checked against the RP2350 data sheet (Figure 2 and the QFN-60
  pin tables), all 61 pins; KiCad's RP2354A symbol matches. The pin table
  lists 54 under IOVDD as well, which is QSPI_IOVDD in every other place.
- Core supply is a switching regulator (data sheet 6.3.8): CIN and COUT
  4.7u, 3.3u fully shielded inductor, VREG_AVDD through 33R / 4.7u, a
  second 4.7u on DVDD pin 23. 0603 25 V X5R parts keep their value at
  3.3 V bias, unlike the 0402 6.3 V parts on the reference design.
- The inductor's orientation matters (its stray field couples into the
  LX/COUT loop and upsets the regulator). Only the polarity-marked Abracon
  AOTA-B201610S3R3-101-T comes on a reel with one orientation. Data sheet
  Figure 26 puts the dot on the VOUT pad, so the project footprint
  `L_Abracon_AOTA-B201610` has pad 1 = dot and the schematic puts pad 1 on
  +1V1, pad 2 on VREG_LX. Copy Figure 26 for the PCB layout.
- Erratum RP2350-E9 (a pad with its input buffer on, sitting between VIL
  and VIH, sources about 120 uA and latches near 2.2 V) is listed for the
  A2 stepping only. DigiKey sells the RP2354A only as A4 (SC1511-A4), so
  R25 (nSLEEP pull-down) keeps 10k. On an A2 part 120 uA would have to
  stay under nSLEEP's 0.9 V threshold, so 6.8k or less. The
  VM_SENSE divider (5.3k source) feeds an ADC pin: firmware must clear the
  pad's input enable on GPIO26 either way (the SDK's adc_gpio_init does).

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
- From the VS Code terminal, `kicad-vis render` dies in inkscape with a
  GLib settings error (`org.gnome.settings-daemon.plugins.xsettings` has no
  key `antialiasing`); it renders with `DISPLAY`, `WAYLAND_DISPLAY` and
  `XDG_DATA_DIRS` unset.

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
Schematic" in the GUI matches by link. The stage still has to be placed:
VS caps at the two VS pin pairs (bridge A 26/30, bridge B 21/25), the
charge pump caps at pins 16..18, R15 and C25 next to pins 3 and 5, J4
beside the OUT pins, and as much GND copper and via area under the EP as
the board allows (see TMC5241 at 48 V).

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
