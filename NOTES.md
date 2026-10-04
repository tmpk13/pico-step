# Notes

## TLE5012B DATA on the shared SPI bus
The ESP32-C5 has one general purpose SPI host (GPSPI2), so the TLE5012B and
the TMC2240 share SCK/MOSI with separate chip selects. The sensor's
half-duplex DATA pin sits on MOSI through the 470R from data sheet Figure 11.
Run the sensor as an SPI device in 3-wire half-duplex mode: the host drives
MOSI for the command word and tri-states it for the read phase, which is the
bidirectional master Figure 11 asks for. The TMC2240 SDO is three-state and
the TLE5012B DATA is high-Z while their selects are inactive, so MISO and
MOSI are free for whichever device is selected. The RP2040 version needed a
4.7k from a TX pin that could not tri-state; that is gone.

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
The ESP32-C5 peaks at 408 mA (802.11a TX at 18 dBm, data sheet Table 5-8),
and the design guidelines ask for a 3.3 V supply of at least 600 mA, which
the AP2112K just meets. At that peak it dissipates ~0.7 W in SOT-23-5 (5 V
in), so sustained TX is a thermal question for the layout (see TODO).

## TMC2240 TQFN32 pin table
pdftotext of the Pin Description table shifts the TSSOP38 column into the
TQFN32 column for PGND ("27, 31"), which would collide with SCK and STEP.
The TQFN pin configuration drawing settles it: the TQFN has no PGND pins,
ground is AGND (4) plus the exposed pad. Symbol pins are tested against the
drawing in `tests/test_footprints.py`.

## TMC2240 pin strapping
- CLK (30) to GND: internal clock. UART_EN (10) to GND: SPI. AIN (2) to GND.
- SLEEPN (25) on GPIO3. Its internal pull-down keeps the driver asleep
  while the ESP32-C5 is in reset; register contents are lost in sleep.
- DRV_ENN (9) on GPIO27 has an internal pull-up, so outputs are off until
  firmware drives it low.
- DIAG0/DIAG1 get 10k pull-ups so open-drain mode works.
- OV (13) left open: no brake chopper.
- ENCA/ENCB/ENCN share the TLE5012B IFA/IFB/IFC nets with GPIO4/5/0, so the
  sensor can be switched to IIF and counted by the driver directly.

## TMC2240 package
DigiKey describes it only as "TQFN"; the data sheet says TQFN32 5x5,
package code T3255+5C. KiCad ships T3255-3/-6/-9 patterns but not -5, and
they differ only in the exposed pad. The project copy uses T3255-3 until
21-0140 is checked.

## ESP32-C5HF4 GPIO budget
The HF4 uses the SPI pins (26..32) for its in-package flash; they are NC.
GPIO11/12 stay on UART0 (header J3, ROM log and download), GPIO13/14 on USB
Serial/JTAG. GPIO15 (SPICS1) is advised against. That leaves GPIO0..10 and
GPIO23..28: 17 pins for 16 signals plus BOOT, which only fits with the TLE5012B
on the shared SPI bus. VM_SENSE must be on GPIO1..6 (ADC1_CH0..5).

## ESP32-C5 strapping pins vs. driver signals
GPIO28 low at reset selects download mode; USB download also needs GPIO27
high (data sheet Table 3-3, with GPIO27=0 and GPIO26=0 the chip enters a
mode where USB Serial/JTAG is disabled). TMC2240 DIAG0 is actively pulled low
while the driver is in reset, and SLEEPN (the driver's reset input) is low
during every ESP32 boot, so DIAG0 must not land on GPIO27. GPIO27 carries
DRV_ENN instead, whose internal pull-up agrees with the strap. The other
straps carry signals whose level at reset does not matter: GPIO26 (DIR) is
read only when GPIO27 is low, GPIO25 (DIAG1) and MTDI (SLEEPN) select SDIO
clock edges, GPIO7 (MOSI) selects the JTAG source only once an eFuse is
burnt, and MTMS (MISO) has no listed strap function. `tests/test_footprints.py`
checks the GPIO27/GPIO28 nets.

Data sheet v1.5 Table 2-8 lists "GPIO27: the VDD_SPI pin"; Table 2-3 and
Table 2-7 put VDD_SPI on GPIO19 (pin 29). The note appears to be a typo.

## Diplexer pin numbering
The ESP32-C5 Hardware Design Guidelines draw the Murata LFD182G45DCHD481
twice with different numbers: Fig. 1 (1 H_PORT, 3 L_PORT, 6 CM, 2/5/7 GND)
and Fig. 7 (4 H_PORT, 6 L_PORT, 2 CM, 1/3/5 GND). Murata spec CD481-01 agrees
with Fig. 1: 1 = P1 high band, 3 = P2 low band, 6 = P3 common, 2/5/7 GND,
4/8 NC with no land at all. The project footprint is the CD481-01 land
pattern turned 90 degrees so terminal 1 is top left.

## RF matching values
The guidelines give only ranges for the chip-side CLC (2.4 GHz: 1.2..3.0 pF,
2.0..3.0 nH; 5 GHz: 0.2..1.5 pF, 0..3 nH) and leave the rest "TBD, varies
with the PCB". The schematic uses mid-range values so the board can be built
and a 0R + two DNP caps at the antenna. Every value has to be tuned on the
assembled board (targets: S11 near 40..45+j0 ohm at 2.4 GHz and 50..65+j0
ohm at 5 GHz, harmonics below -35 dB). 0201 parts per the guidelines.

## kicad-vis and large MCU symbols
- kicad-vis treats stacked (hidden duplicate) pins as separate pins and
  labels each one, so the ESP32-C5 and diplexer GND pins are spread out with
  one grid of space instead of stacked.
- A column of supply pins on the side of a symbol fans out into risers one
  grid apart and the rail names overlap. The ESP32-C5 symbol puts supply
  pins on the top edge one grid apart, with a wider gap in the middle where
  kicad-vis centers the reference designator.
- When an MCU pin row lines up with a pin row on another part of the same
  net, kicad-vis draws a straight wire and drops the net name onto the far
  part's pin names. GPIO8 got the LED for that reason (STEP/DIR on GPIO8
  overlapped U5's STEP/DIR names).
