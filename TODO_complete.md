# Completed

- RP2040 core, USB-C + 3V3 LDO, TLE5012B on SPI1, VM input + sense: schematic generated, ERC clean.
- Project footprints: Infineon PG-DSO-8 (data sheet land pattern), USB4105 with SH shield pads.
- TMC2240: symbol from data sheet pin table (all 33 pins tested), driver block per Figure 35, motor connector J4.
- MCU swapped RP2040 -> ESP32-C5HF4: symbol from data sheet v1.5 (49 pins tested), supply/crystal/CHIP_PU/BOOT per Espressif reference, RF CLC + Murata diplexer (land pattern from spec CD481-01) + U.FL, TLE5012B moved onto the shared SPI bus, strapping-pin rules tested.
- RF path parts renamed with `_rf` suffix (generator, schematic, PCB, BOM/DigiKey docs); parts-by-chip list in PARTS_BY_CHIP.md; reference consistency tests.
- MCU swapped back ESP32-C5HF4 -> RP2040 (generator, symbols, footprints, tests and docs as before the swap; ESP32 version kept in git at 738db68). DigiKey list and parts-by-chip list redone for RP2040 (56 parts), order list coverage test.
- Hand-placed schematic restored (738db68) with the ESP32 block removed and the RP2040 block pasted below; ERC clean, netlist matches circuit.py apart from the existing hand edits. `mise run sch` now writes to build/, `mise run parity` added.
- Driver swapped TMC2240 -> TMC5160A-TA for VM up to 48 V: symbol from data sheet rev 1.18 (49 pins tested), stock TQFP-48-EP footprint (EP matches the data sheet), 8x CSD19537Q3 bridges with 0.1R sense, Figure 3.1 support parts, per-bridge wiring test. Pasted in place into the hand-placed schematic (A1 sheet), ERC clean, parity shows only the existing hand edits. VM parts re-rated for 48 V (C19 63 V, VM_SENSE 100k/5.6k). DigiKey list 82 parts.
- Dropped: TMC2240 TQFN exposed pad check (part removed).
