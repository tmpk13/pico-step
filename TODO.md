# TODO

- [ ] TMC2240: obtain data sheet (analog.com download blocked in agent
      sandbox), then make symbol + TQFN-36 footprint from its pin table and
      land pattern, add driver block (VS decoupling, VCP/CPI/CPO charge pump,
      5VOUT, IREF resistor, motor connector) to `tools/circuit.py`.
- [ ] Motor connector J4 (A1/A2/B1/B2).
- [ ] Choose passive MPNs (all passives are value-only today).
- [ ] PCB: TLE5012B must sit on the motor shaft axis, diametric magnet.
