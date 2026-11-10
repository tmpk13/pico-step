# Encoder, USB, power and MCU

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
The KiCad 10.0.3 AppImage library names the USB-C shield pin and the GCT
USB4105 footprint pads "SH"; the system KiCad 10.0.4 library names both
"S1". Mixing the two leaves the shield pads with no net and no check
reports it. The project carries its own footprint copy with "SH" pads, the
drawing names J1's shield pin SH, and `tests/test_footprints.py` checks
that every schematic pin exists as a pad on its footprint and vice versa.

`tools/footprints.py` rebuilds that copy from the system library. Under the
current system library the result also differs from the committed file
(shield pads `pad_prop_mechanical` instead of `pad_prop_heatsink`, NPTH
layers `*.Cu`), and the board's J1 then fails DRC's library match. So
`mise run sch` no longer runs it; `mise run footprints` stays a separate,
deliberate step.

## Power
Logic is USB powered (VBUS -> AP2112K-3.3). Motor supply VM enters on J2,
is not tied to VBUS, and runs up to 48 V. VM_SENSE (100k/5.6k) puts 48 V at
2.55 V and reaches the 3.3 V ADC limit at 62 V, about the 63 V rating of
the bulk capacitors (the TMC5241 itself runs to 65 V). Every part on VM is
rated 63 V or more.

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
