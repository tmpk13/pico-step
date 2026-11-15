# pico-step

Closed-loop stepper driver: RP2354A + TMC5241 motion controller and
driver (integrated 65 V bridges) + TLE5012B magnetic angle sensor.
USB-C powered logic, separate motor supply (VM) up to 48 V.

The design is a stack of three boards, each a KiCad project in its own
folder: `mcu/` (RP2354A, USB-C, 3.3 V), `encoder/` (TLE5012B) and
`driver/` (TMC5241, motor supply input). They join through one 2x12 bus
header, J5, drawn once in `stack/stack.tsch` and carried by every board.
Each board's schematic is drawn as text in `<board>/tsch/` for the
text-schematic tool `tsch` (set `TSCH` to its binary when it is not on the
PATH); `mise run sch` builds them into `<board>/*.kicad_sch`, which are
generated and not committed. Each board's `.kicad_pcb` is still an uncut
copy of the one-board layout, `pico-step.kicad_pcb`.

```sh
mise run install   # test deps
mise run sch-check # check every board's tsch/ drawing (fast, no KiCad)
mise run sch       # <board>/tsch/ -> <board>/*.kicad_sch, proven with kicad-cli
mise run erc
mise run test
mise run render    # build/tsch/<board>/*.png
mise run pcb-sync mcu # one board <- its schematic (footprints, values, nets), keeps placement
mise run pcb-place # placement table -> board (overwrites GUI moves)
mise run pcb-dsn   # build/pico-step.dsn for freerouting
mise run pcb-autoroute # FREEROUTING=<launcher or jar> freerouting -> build/pico-step.ses
mise run pcb-ses   # import the session and refill zones
mise run pcb-gnd   # GND stitching vias after routing
mise run pcb-drc
mise run pcb-render # build/pcb-top.png, build/pcb-bottom.png
```

The one-board PCB, `pico-step.kicad_pcb`, is a 42 mm NEMA17 back-mount,
2 layers, 0.15 mm rules; its floor plan is in `notes/pcb.md`. The pcb-*
tasks other than pcb-sync still work on it, not on the board folders.

See `ARCHITECTURE.md` for the block diagram, `BOM.md` for sourced parts,
`PARTS_BY_CHIP.md` for which parts support which chip,
`DIGIKEY.md` for the order list,
`TODO.md` for open work.
