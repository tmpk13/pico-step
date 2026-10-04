# TODO

- [ ] TMC2240 footprint exposed pad: confirm T3255-5 EP size against Maxim
      outline 21-0140 / land pattern 90-0013 (not in the TMC2240 data sheet;
      `ref/` has only the data sheet). Footprint currently copies T3255-3
      (EP 3.1 x 3.1 mm); update `STOCK_COPIES` in `tools/footprints.py`.
- [ ] Choose passive MPNs (all passives are value-only today).
- [ ] PCB: TLE5012B on the motor shaft axis, diametric magnet; TMC2240 EP
      with many GND vias, VS caps at the VS pins.
- [ ] PCB: "Update PCB from Schematic" for the ESP32-C5 swap (RP2040, its
      flash and 12 MHz crystal leave; U1 QFN-48, RF section, FL1, J5 arrive).
- [ ] PCB RF: 50 ohm coplanar lines ANT_2G/ANT_5G -> FL1 -> J5, matching
      parts next to the chip, stub to ground on C31 (5 GHz shunt at the chip),
      ground vias around the RF path, crystal away from the RF lines.
- [ ] RF tuning on the assembled board with a VNA: C29/L3/C30 (2.4 GHz),
      C31/L4/C32 (5 GHz), C33/R18/C34 (antenna). Crystal C27/C28 trimmed to
      +-10 ppm with a TX tone test.
- [ ] Source FL1 in small quantity (DigiKey sells reels of 4000 only).
- [ ] 3V3 regulator thermal: AP2112K in SOT-23-5 at the 408 mA TX peak is
      ~0.7 W from 5 V. Check the layout copper, or move to a SOT-89/SOT-223
      LDO or a buck if Wi-Fi TX is sustained.
- [ ] Choose the external dual-band (2.4 + 5 GHz) antenna for J5.
