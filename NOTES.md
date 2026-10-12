# Notes

## TLE5012B DATA line on an RP2040 SPI master
The sensor's SSC DATA pin is half duplex. The data sheet (Figure 11) wants
470R on DATA and a master whose TX tri-states. RP2040 SPI TX never
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
  36 V x (8 x 16 nC x 40 kHz) = 0.2 W (limit 0.5 W), 5 V regulator
  43 V x 10 mA = 0.45 W (limit 1 W). An external 12 V gate supply on
  VSA/12VOUT (Figure 3.2) is the fallback if the IC runs hot.
- No overvoltage clamp on VM. A TVS that stands off 48 V clamps above the
  60 V maximum, so regenerative energy (fast deceleration, driver disabled
  while the motor spins) must go into the supply or a brake circuit.

## MOSFETs and sense resistors
- CSD19537Q3: 100 V (48 V plus margin for ringing), 12.1 mOhm, Qg 16 nC,
  Qgd 2.9 nC. Miller charge under 10 nC runs at DRVSTRENGTH=0 with no gate
  resistor (section 3.3); bootstrap 220 nF for Qg < 20 nC (Figure 3.1).
  Pinout checked against TI's top view: 1-3 S, 4 G, 5-8 and tab D, which is
  the stock symbol and NexFET footprint numbering.
- RSENSE 0.1 Ohm: 2.3 A RMS / 3.3 A peak at full scale (data sheet table,
  chapter 9). Chosen to stay inside the JST XH motor header's 3 A rating;
  firmware sets the actual current with GLOBALSCALER and IRUN. More current
  needs a lower RSENSE and a bigger motor connector. Standstill peak
  dissipation 1.1 W, so 3 W 2512 parts.
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
  the RP2040's ~50k reset pull-down holds 2.75 V, above VIH = 0.7 x VCC_IO
  = 2.31 V, so the bridges stay off until firmware drives GPIO8 low.
- DIAG0/DIAG1 keep 10k pull-ups (open drain needs 47k or less).
- The exposed pad is pin 49 (GNDD/GNDP, low side gate driver ground).

## MCU choice
The board went RP2040 -> ESP32-C5HF4 -> RP2040. The ESP32-C5 version
(dual-band Wi-Fi, RF diplexer, TLE5012B on a shared 3-wire SPI bus, strap
rules) is commit eee3e1e plus 1840e9d; 738db68 holds its schematic and PCB
placement. Swapping back restored the generator, symbols, footprints and
tests from b46301c. The PCB still carries the ESP32 footprints and needs
Update PCB from Schematic; the shared references (C3.., R3.., Y1) mean
different parts now, so check the placement of every reused reference.

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

## DigiKey list
- eparts-search returns the reel (TR) variant of most passives; use the MPN in
  the DigiKey list upload so packaging can be chosen there.
- Two first-choice Murata MPNs were obsolete (100n 50V 0603, 10u 0805);
  alternates are in DIGIKEY.md.
- `tests/test_refs.py` checks that the order list names every generator
  reference exactly once and that quantities add up.
