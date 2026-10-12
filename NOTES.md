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
2.55 V and reaches the 3.3 V ADC limit only at 62 V, past the driver's
60 V absolute maximum. Every part on VM is rated 63 V or more.

## TMC5160A data sheet
`ref/tmc5240.pdf` is the TMC5240 (36 V, integrated FETs), not the TMC5160.
The TMC5160A data sheet rev 1.18 was downloaded from analog.com into
`ref/tmc5160a_datasheet.pdf` (analog.com resets plain curl requests; a
browser user agent and Accept header got through).
The TMC2240 version of the board (36 V, integrated FETs) is commit d537741.
C21..C26 and R15..R17 kept their numbers but are different parts now.

## TMC5160A at 48 V
- Operating range: VS 10..55 V, VSA 10..50 V; absolute maximum 60 V
  (64 V short peaks). Keep the supply at or below 50 V with VSA tied to VS.
- VSA is tied to VS (standard circuit, Figure 3.1). Section 3.2 allows that
  at 48 V when MOSFET Qg < 50 nC, chopper <= 40 kHz and the clock is the
  internal 12 MHz. Estimated regulator dissipation at 48 V: 12 V regulator
  36 V x (8 x 8 nC x 40 kHz) = 0.09 W (limit 0.5 W), 5 V regulator
  43 V x 10 mA = 0.45 W (limit 1 W). An external 12 V gate supply on
  VSA/12VOUT (Figure 3.2) is the fallback if the IC runs hot.
- No overvoltage clamp on VM. A TVS that stands off 48 V clamps above the
  60 V maximum, so regenerative energy (fast deceleration, driver disabled
  while the motor spins) must go into the supply or a brake circuit.

## MOSFETs and sense resistors
- SQJB68EP-T1_BE3 (Vishay dual N, PowerPAK SO-8L Dual), one per half
  bridge: 100 V, 92 mOhm max (162 mOhm at 125 C), Qg 4.7 nC typ / 8 nC
  max, Qgd 1.3 nC, Vgs +-20 V, RthJA 85 C/W on 1 in^2. Chosen over the
  CSD19537Q3 (12 mOhm, $1.39 at 40 pcs) for cost at 5-board quantities:
  4 duals cost $14 against $56 for 8 singles (Mouser, 2026-10-12). The
  CSD19538Q3A (59 mOhm single) was cheaper still but listed no stock.
  Miller charge under 10 nC: DRVSTRENGTH=0, no gate resistor (section 3.3);
  bootstrap 220 nF for Qg < 20 nC (Figure 3.1).
- Pinout from the SQJB68EP data sheet page 1 and the case outline (doc
  66934): top view with the leads at the bottom, pins 1..4 left to right
  are S1 G1 S2 G2; drain paddle D1 is over pins 1-2, D2 over pins 3-4.
  Footprint pads: D1 = 6, D2 = 5, matching KiCad's
  Q_Dual_NMOS_S1G1S2G2D2D1 (unit 1 = pins 1 2 6, unit 2 = pins 3 4 5).
  FET1 is the high side, FET2 the low side; S1 (pin 1) and D2 (right
  paddle) must be joined on the board, which crosses the package.
- Footprint pads from Vishay doc 63817 (minimum pads, PowerPAK SO-8L
  Dual), y shifted +0.18 mm so the 4.90 x 4.37 mm body is centered. Each
  drain paddle is three same-numbered pads (paddle plus two side tabs).
  Paste covers the whole paddle; reduce it if the first boards float.
- In the hand-placed schematic each old single FET became one unit at the
  same position (identical G/D/S pin geometry), so no wires moved:
  Q1 Q2 -> Q1 units 1 2, Q3 Q4 -> Q2, Q5 Q6 -> Q3, Q7 Q8 -> Q4.
- RSENSE 0.15 Ohm (Stackpole CSRN2512FTR150, 2 W): 1.6 A RMS / 2.2 A peak
  at full scale (data sheet table, chapter 9). The cap comes from the
  FETs: at standstill one low side FET can carry the peak continuously,
  2.2^2 x 0.15 Ohm (hot) = 0.7 W, about 60 C over ambient at 85 C/W. The
  sense resistor sees the same 0.7 W. More current needs lower-resistance
  FETs as well as a lower RSENSE.
- Short detection must be desensitized for the higher on-resistance. At
  2.2 A peak the low side check sees 0.36 V (hot FET) + 0.33 V (RSENSE) =
  0.69 V, above the 0.55 V minimum of S2VS_LEVEL=6 (OTP default 6 or 12).
  Use S2VS_LEVEL >= 9 (about 0.83 V minimum) and S2G_LEVEL >= 8 (high side
  drop 0.36 V; level 6 minimum is 0.46 V). Levels interpolated linearly
  between the data sheet's level 6 and level 15 limits.
- 12VOUT uses a 1206 X7R 10 uF 25 V: at 12 V bias an 0805 10 uF keeps too
  little of its value for the ">= 10x one bootstrap capacitor" rule.

## TMC5160A pin strapping
- SPI_MODE (22) high: SPI. TST_MODE (11) and CLK (12) to GND.
- SD_MODE (21) is on GPIO18 (freed by the TMC2240's SLEEPN) with a 10k
  pull-down. Low: internal ramp generator, ENCA/ENCB/ENCN are encoder
  inputs, REFL/REFR are reference switch inputs. High: STEP/DIR on GPIO6/7,
  and the same ENC pins become DcStep enable, DcStep gating and the DCO
  output. The data sheet only describes SD_MODE as a strap; whether it can
  change while VCC is up is untested, so set it before VM comes up.
- ENCN_DCO is an output with SD_MODE high, so it reaches the TLE5012B IFC
  net through 1k. With SD_MODE high keep the TLE5012B IIF outputs off, or
  IFB enables DcStep.
- DRV_ENN (28) has no internal pull (the TMC2240's did). 10k to 3V3 against
  the MCU's ~50k reset pull-down holds 2.75 V, above VIH = 0.7 x VCC_IO
  = 2.31 V, so the bridges stay off until firmware drives GPIO8 low.
- DIAG0/DIAG1 keep 10k pull-ups (open drain needs 47k or less).
- The exposed pad is pin 49 (GNDD/GNDP, low side gate driver ground).

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
  R25 (SD_MODE) keeps 10k. On an A2 part it would need 8.2k or less. The
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

## DigiKey list
- eparts-search returns the reel (TR) variant of most passives; use the MPN in
  the DigiKey list upload so packaging can be chosen there.
- Two first-choice Murata MPNs were obsolete (100n 50V 0603, 10u 0805);
  alternates are in DIGIKEY.md.
- `tests/test_refs.py` checks that the order list names every generator
  reference exactly once and that quantities add up.

## PCB floor plan
The 42.2 mm square with 31 mm hole spacing is a NEMA17 back-mount: U3 sits
on the back at the shaft axis (100, 100). The back faces the motor, so it
only carries parts under 1.2 mm tall (U1 with its regulator, decoupling and
pull resistors, U3 and its series resistors, the USB CC and LDO parts
under J1). Keep a 6 mm radius around the center on the back free for the
shaft magnet; nothing but U3 is inside it. M3 heads need about 3 mm radius
around each hole on both sides.

Top side, top to bottom: J4 and the two buttons on the top edge, the four
dual FETs in a row (Q3 Q4 Q1 Q2 = 1B 2B 1A 2A, the order of U5's gate
pins), R18 and R15 under them, U5, then J2, the crystal and J3 on the
bottom edge. C19 (J2 side) and C35 (VM side) are the only parts that take
the left and right edges below the FET row; J1 sits at the right edge
beside the FET row. The placement is a table in `tools/pcb_place.py`;
re-running it overwrites GUI moves.

- U5 is shifted right (x 103.9) and down (y 105.0) so its thermal vias and
  back pad clear U3's pads on the back; its gate edge faces the FET row.
- Each SQJB68EP's S1 lead is joined to the D2 paddle by a 0.5 mm trace
  around the left side of the package and over the top (the data sheet
  wants a pour, but the lead row and the D1 paddle block the direct way).
  The FET pitch is 6.2 mm to leave a 1 mm gap for that trace between
  neighbors. VM reaches the D1 paddles through two 0.8 mm vias each from
  a pour on the back under the row.
- J4's pin order 1A 2A 1B 2B against the FET order means the pairs cross:
  phase A outputs run on the top at y 83.6 and 84.5, phase B on the back at
  y 84.2 and 85.4, through vias at the ends of the output runs.
- Low side sources: Q3's goes straight into R18's hot pad; Q4, Q1 and Q2
  cross the gate fan-out on the back through 1.0 mm vias, ending in a via
  inside the resistor's hot pad.
- SRAH/SRBH (R19, R21) start at the sense resistors' hot pads (true
  Kelvin). SRAL/SRBL (R20, R22) return through the GND plane, not a Kelvin
  trace to the resistor's GND pad: at 2 A the plane drop over a few mm is
  about 1 mV against 330 mV full scale.
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
- Freerouting routes the rest. `tools/pcb_route.py` locks its copper, the
  Specctra export writes locked tracks as `(type fix)`, and the planes (GND
  on both layers, VM on the back) are exported as conduction areas, so the
  autorouter neither moves them nor routes GND.
- Freerouting 2.1.0 from the CLI still opens its GUI; with an empty
  profile email it then shows a modal User Settings dialog after routing
  and never writes the session file (it also opens the GUI on whatever
  DISPLAY is set, and dies with HeadlessException without one). With
  logging on it looked like a hang at "traces not 45 degree".
  `tools/freerouting_profile.py` writes a dummy email into
  /tmp/freerouting/freerouting.json, telemetry off, before each run.
- The TQFP-48 ThermalVias footprint has 0.2 mm via drills; the board rule
  and the fab want 0.3 mm, so `tools/pcb_route.py` widens them to 0.6/0.3 in
  place (DRC then reports a library mismatch for U5, expected).
- Net-(J2-Pin_1) is still split from VM (see "Power?"): J2 pin 1 is wired
  to C19 only. The link to VM is one short trace from C19's + pad to the
  VM pour's left arm once the schematic decides.

## Routing result
Pipeline: `pcb-place`, `pcb-route`, `pcb-fill`, `pcb-dsn`, `pcb-autoroute`,
`pcb-ses`, `pcb-gnd`, `pcb-drc`. The power stage and VM distribution are
hand-routed (locked); freerouting 2.1.0 routes the signals with 0.15 mm
rules and 0.5 mm vias in about four minutes for 30 passes. Over six
placement variants it never got below about 25 open signal connections
of 142; its result also varies by about 10 between runs on similar
inputs. The open ones cluster at U5's left edge (12VOUT, 5VOUT, CB1,
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
