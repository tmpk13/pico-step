# BOM (sourced via DigiKey, 2026-10-02; MCU swap 2026-10-03)

| Ref | MPN | Manufacturer | Footprint | Stock | Unit price |
| --- | --- | --- | --- | --- | --- |
| U1 | ESP32-C5HF4 | Espressif Systems | Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.66x4.66mm_ThermalVias | 2208 | $3.62 @1 cut tape |
| U2 | AP2112K-3.3TRG1 | Diodes Inc. | Package_TO_SOT_SMD:SOT-23-5 | 435354 | $0.113 @3000 reel |
| U3 | TLE5012BE5000XUMA1 | Infineon | pico-step:Infineon_PG-DSO-8 | 17056 | $2.40 @2500 reel |
| Y1 | FL4800069 (48 MHz, +-10 ppm, CL 8 pF) | Diodes Inc. | Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm | 1165 | $0.75 @1 cut tape |
| FL1 | LFD182G45DCHD481 (2.4/5 GHz diplexer) | Murata | pico-step:Murata_LFD182G45DCHD481 | reel only, MOQ 4000 | $0.114 @4000 |
| J5 | U.FL-R-SMT-1(10) (6 GHz) | Hirose | Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical | 389396 | $0.96 @2500 reel |
| J1 | USB4105-GF-A | GCT | pico-step:USB_C_Receptacle_GCT_USB4105-xx-A_16P_SH | 116353 | $0.50 @800 reel |
| U5 | TMC2240ATJ+T (TQFN-32 5x5, T3255+5C) | Analog Devices | pico-step:Maxim_TQFN-32-1EP_5x5mm_P0.5mm_T3255-5 (provisional EP) | 1465 | $8.90 @1 |
| J4 | JST B4B-XH-A (motor) | JST | Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical | not searched | |

Notes:
- The ESP32-C5HF4 has 4 MB flash in the package; the RP2040's W25Q128 flash
  and 12 MHz crystal are gone.
- FL1 is reel-only at DigiKey (MOQ 4000); prototypes need another source.
- RF matching parts (C29..C34, L3, L4, R18) and the VDDA1/2 filter (L1 2.0 nH
  500 mA, C13, C14) are value-only 0201 parts; the RF values are starting
  points to be tuned.
- Only DigiKey is configured in eparts-search; LCSC and Mouser were not queried.
- Several MPNs above are reel-only at DigiKey; cut tape variants exist for prototypes.
