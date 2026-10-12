# pico-step

Closed-loop stepper driver board: RP2354A + TMC5160A motion controller and
gate driver (four external dual MOSFETs) + TLE5012B magnetic angle sensor.
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
mise run pcb-place # placement table -> board (overwrites GUI moves)
mise run pcb-route # locked power stage copper and VM pour (before autorouting)
mise run pcb-dsn   # build/pico-step.dsn for freerouting
mise run pcb-autoroute # FREEROUTING=<launcher or jar> freerouting -> build/pico-step.ses
mise run pcb-ses   # import the session and refill zones
mise run pcb-gnd   # GND stitching vias after routing
mise run pcb-drc
mise run pcb-render # build/pcb-top.png, build/pcb-bottom.png
```

The PCB is a 42 mm NEMA17 back-mount, 2 layers, 0.15 mm rules; the floor
plan is in `NOTES.md`.

See `ARCHITECTURE.md` for the block diagram, `BOM.md` for sourced parts,
`PARTS_BY_CHIP.md` for which parts support which chip,
`DIGIKEY.md` for the order list,
`TODO.md` for open work.
