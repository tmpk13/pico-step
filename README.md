# pico-step

Closed-loop stepper driver board: ESP32-C5HF4 (dual-band Wi-Fi 6, BLE) +
TMC2240 driver + TLE5012B magnetic angle sensor, USB-C powered logic,
separate motor supply (VM), U.FL antenna port.

The schematic is generated; edit `tools/circuit.py`, not the `.kicad_sch`.

```sh
mise run install   # test deps
mise run sch       # footprints + schematic + ERC severities
mise run erc
mise run test
mise run render    # build/pico-step.png
```

See `ARCHITECTURE.md` for the block diagram, `BOM.md` for sourced parts,
`TODO.md` for open work.
