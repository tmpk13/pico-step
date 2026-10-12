# pico-step

Closed-loop stepper driver board: RP2354A + TMC5160A motion controller and
gate driver (eight external MOSFETs) + TLE5012B magnetic angle sensor.
USB-C powered logic, separate motor supply (VM) up to 48 V.

The schematic is placed by hand in KiCad. `tools/circuit.py` is the reference
netlist; `mise run parity` lists where the two differ.

```sh
mise run install   # test deps
mise run sch       # footprints + build/pico-step.gen.kicad_sch + ERC severities
mise run parity    # schematic nets vs tools/circuit.py
mise run erc
mise run test
mise run render    # build/pico-step.png
```

See `ARCHITECTURE.md` for the block diagram, `BOM.md` for sourced parts,
`PARTS_BY_CHIP.md` for which parts support which chip,
`DIGIKEY.md` for the order list,
`TODO.md` for open work.
