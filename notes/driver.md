# TMC5241 driver

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

## TMC5241-EVKIT reference
`ref/tmc5241-evkit.pdf` (user guide rev 0) has the schematic (page 12),
BOM and placement (Figure 5) of ADI's board. IC301 sits in the same
orientation as our footprint, pin 1 at the top left.
- VS: the four pins (VS1..VS4 = 21, 25, 26, 30) are one +VM net, with no
  pin assigned to a bridge. Two 100n/100V 0603 and two 1u/100V 0805
  ceramics sit on that net, placed as one 100n + 1u pair at each end of
  the VS/OUT side: C305/C307 at the pin 30/31 corner, C306/C308 at the pin
  20/21 corner. Nothing sits on the top side at the middle pair 25/26.
  The drawing shows no copper, so how 25/26 join the ends (and the layer
  count) is not visible.
- Charge pump: C304 1u/16V VCP-VS and C303 22n/100V CPI-CPO, both under
  the bottom row near pins 16..18. The 100 V CPI-CPO part agrees with ours.
- Left side: C302 2.2u (VDD1V8) and C301 100n (VCC_IO).
- Bulk: two 150u/100V electrolytics (Panasonic EEU-FS2A151), one above
  and one below the IC, and an SMCJ54A TVS at the supply input.
- Brake output: OV drives the gate of a DMN10H220L-7 (100 V, SOT-23) with
  a 24k pull-up to a 5 V rail made from VM; the brake resistor is
  external on J303 between VM and the drain, with a PMEG10010 diode across
  it and a 5k6 1 W + LED indicator.

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
