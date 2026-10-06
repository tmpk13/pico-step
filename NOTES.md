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
Logic is USB powered (VBUS -> AP2112K-3.3). Motor supply VM enters on J2 and
is not tied to VBUS; VM_SENSE (100k/10k, 36 V -> 3.27 V) lets firmware see it.

## TMC2240 TQFN32 pin table
pdftotext of the Pin Description table shifts the TSSOP38 column into the
TQFN32 column for PGND ("27, 31"), which would collide with SCK and STEP.
The TQFN pin configuration drawing settles it: the TQFN has no PGND pins,
ground is AGND (4) plus the exposed pad. Symbol pins are tested against the
drawing in `tests/test_footprints.py`.

## TMC2240 pin strapping
- CLK (30) to GND: internal clock. UART_EN (10) to GND: SPI. AIN (2) to GND.
- SLEEPN (25) on GPIO18. Its internal pull-down keeps the driver asleep
  while the RP2040 is in reset; register contents are lost in sleep.
- DRV_ENN (9) has an internal pull-up, so outputs are off until firmware
  drives GPIO8 low.
- DIAG0/DIAG1 get 10k pull-ups so open-drain mode works.
- OV (13) left open: no brake chopper.
- ENCA/ENCB/ENCN share the TLE5012B IFA/IFB/IFC nets with GPIO14..16, so the
  sensor can be switched to IIF and counted by the driver directly.

## TMC2240 package
DigiKey describes it only as "TQFN"; the data sheet says TQFN32 5x5,
package code T3255+5C. KiCad ships T3255-3/-6/-9 patterns but not -5, and
they differ only in the exposed pad. The project copy uses T3255-3 until
21-0140 is checked.

## MCU choice
The board went RP2040 -> ESP32-C5HF4 -> RP2040. The ESP32-C5 version
(dual-band Wi-Fi, RF diplexer, TLE5012B on a shared 3-wire SPI bus, strap
rules) is commit eee3e1e plus 1840e9d; 738db68 holds its schematic and PCB
placement. Swapping back restored the generator, symbols, footprints and
tests from b46301c and regenerated the schematic. The PCB was left alone:
its footprints come from the ESP32 netlist and the shared references
(C3.., R3.., Y1) mean different parts now, so it needs Update PCB from
Schematic in KiCad, then a placement check of every reused reference.

## DigiKey list
- eparts-search returns the reel (TR) variant of most passives; use the MPN in
  the DigiKey list upload so packaging can be chosen there.
- Two first-choice Murata MPNs were obsolete (100n 50V 0603, 10u 0805);
  alternates are in DIGIKEY.md.
- `tests/test_refs.py` checks that the order list names every generator
  reference exactly once and that quantities add up.
