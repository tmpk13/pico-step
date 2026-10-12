# BOM (sourced via DigiKey, 2026-10-02; driver stage and RP2354A 2026-10-11; bridge FETs and RSENSE 2026-10-12, DigiKey and Mouser)

| Ref | MPN | Manufacturer | Footprint | Stock | Unit price |
| --- | --- | --- | --- | --- | --- |
| U1 | SC1511-A4 (RP2354A, A4 stepping) | Raspberry Pi | Package_DFN_QFN:QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm | 3303 | $1.10 @500 reel |
| L1 | AOTA-B201610S3R3-101-T (3.3u, polarity marked) | Abracon | pico-step:L_Abracon_AOTA-B201610 | 26266 | $0.109 @3000 reel |
| C11, C12, C17, C36 | GRM188R61E475KE11D (4.7u 25V X5R) | Murata | Capacitor_SMD:C_0603_1608Metric | 749278 | $0.052 @4000 reel |
| U2 | AP2112K-3.3TRG1 | Diodes Inc. | Package_TO_SOT_SMD:SOT-23-5 | 435354 | $0.113 @3000 reel |
| U3 | TLE5012BE5000XUMA1 | Infineon | pico-step:Infineon_PG-DSO-8 | 17056 | $2.40 @2500 reel |
| Y1 | ABM8-272-T3 (12 MHz, CL 10 pF) | Abracon | Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm | 28279 | $0.42 @3000 reel |
| J1 | USB4105-GF-A | GCT | pico-step:USB_C_Receptacle_GCT_USB4105-xx-A_16P_SH | 116353 | $0.50 @800 reel |
| U5 | TMC5160A-TA (TQFP-48-EP 7x7, EP 5x5) | Analog Devices | Package_QFP:TQFP-48-1EP_7x7mm_P0.5mm_EP5x5mm_ThermalVias | 665 | $10.57 @1 |
| Q1..Q4 | SQJB68EP-T1_BE3 (dual N, 100 V, 92 mOhm, Qg 8 nC max) | Vishay Siliconix | pico-step:Vishay_PowerPAK_SO-8L_Dual | 7806 Mouser, 1009 DigiKey | $0.706 @10 Mouser |
| R15, R18 | CSRN2512FTR150 (0.15R 2W) | Stackpole | Resistor_SMD:R_2512_6332Metric | 3000 | $0.319 @10 cut tape |
| C19, C35 | 63SGV100M10X10.5 (100u 63V) | Rubycon | Capacitor_SMD:CP_Elec_10x10.5 | 8760 | $0.41 @500 reel |
| J4 | JST B4B-XH-A (motor) | JST | Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical | not searched | |

Notes:
- Only DigiKey is configured in eparts-search; LCSC and Mouser were not queried.
- Several MPNs above are reel-only at DigiKey; cut tape variants exist for prototypes.
