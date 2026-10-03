# TODO

- [ ] TMC2240 footprint exposed pad: confirm T3255-5 EP size against Maxim
      outline 21-0140 / land pattern 90-0013 (not in the TMC2240 data sheet;
      `ref/` has only the data sheet). Footprint currently copies T3255-3
      (EP 3.1 x 3.1 mm); update `STOCK_COPIES` in `tools/footprints.py`.
- [ ] Choose passive MPNs (all passives are value-only today).
- [ ] PCB: TLE5012B on the motor shaft axis, diametric magnet; TMC2240 EP
      with many GND vias, VS caps at the VS pins.
