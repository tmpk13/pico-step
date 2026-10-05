# Completed

- RP2040 core, USB-C + 3V3 LDO, TLE5012B on SPI1, VM input + sense: schematic generated, ERC clean.
- Project footprints: Infineon PG-DSO-8 (data sheet land pattern), USB4105 with SH shield pads.
- TMC2240: symbol from data sheet pin table (all 33 pins tested), driver block per Figure 35, motor connector J4.
- MCU swapped RP2040 -> ESP32-C5HF4: symbol from data sheet v1.5 (49 pins tested), supply/crystal/CHIP_PU/BOOT per Espressif reference, RF CLC + Murata diplexer (land pattern from spec CD481-01) + U.FL, TLE5012B moved onto the shared SPI bus, strapping-pin rules tested.
- RF path parts renamed with `_rf` suffix (generator, schematic, PCB, BOM/DigiKey docs); parts-by-chip list in PARTS_BY_CHIP.md; reference consistency tests.
