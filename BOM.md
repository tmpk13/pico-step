# BOM (sourced via DigiKey, 2026-10-02; driver stage 2026-10-11)

| Ref | MPN | Manufacturer | Footprint | Stock | Unit price |
| --- | --- | --- | --- | --- | --- |
| U1 | SC0914(13) (RP2040) | Raspberry Pi | Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm | 134816 | $0.70 @3400 reel |
| U2 | AP2112K-3.3TRG1 | Diodes Inc. | Package_TO_SOT_SMD:SOT-23-5 | 435354 | $0.113 @3000 reel |
| U3 | TLE5012BE5000XUMA1 | Infineon | pico-step:Infineon_PG-DSO-8 | 17056 | $2.40 @2500 reel |
| U4 | W25Q128JVSIQ | Winbond | Package_SO:SOIC-8_5.3x5.3mm_P1.27mm | 46429 | $3.60 @1 |
| Y1 | ABM8-272-T3 (12 MHz, CL 10 pF) | Abracon | Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm | 28279 | $0.42 @3000 reel |
| J1 | USB4105-GF-A | GCT | pico-step:USB_C_Receptacle_GCT_USB4105-xx-A_16P_SH | 116353 | $0.50 @800 reel |
| U5 | TMC5160A-TA (TQFP-48-EP 7x7, EP 5x5) | Analog Devices | Package_QFP:TQFP-48-1EP_7x7mm_P0.5mm_EP5x5mm_ThermalVias | 665 | $10.57 @1 |
| Q1..Q8 | CSD19537Q3 (100 V, 12.1 mOhm, Qg 16 nC) | Texas Instruments | Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET | 66486 | $0.60 @2500 reel |
| R15, R18 | CRA2512-FZ-R100ELF (0.1R 3W) | Bourns | Resistor_SMD:R_2512_6332Metric | 94837 | $0.16 @4000 reel |
| C19, C35 | 63SGV100M10X10.5 (100u 63V) | Rubycon | Capacitor_SMD:CP_Elec_10x10.5 | 8760 | $0.41 @500 reel |
| J4 | JST B4B-XH-A (motor) | JST | Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical | not searched | |

Notes:
- W25Q16JVSSIQ was the first flash choice; DigiKey lists it Obsolete.
- Only DigiKey is configured in eparts-search; LCSC and Mouser were not queried.
- Several MPNs above are reel-only at DigiKey; cut tape variants exist for prototypes.
