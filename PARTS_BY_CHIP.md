# Parts by chip

Every one of the 69 parts on the board, grouped by the chip it supports.
Parts with an `_rf` suffix are on the ESP32-C5 antenna path.

## U1 ESP32-C5HF4

| Function | Parts |
| --- | --- |
| Decoupling, VDDA6/VDDA7 | C3 10u, C4 0.8p, C5 0.3p |
| Decoupling, VDDA8 | C6 1u |
| Decoupling, VDDPST1/2/3 | C7 1u, C8 100n, C12 100n |
| Decoupling, VDDA5 | C9 1u |
| Decoupling, VDDA3/VDDA4 | C10 10n, C11 100n |
| VDDA1/VDDA2 LC filter (PA harmonics) | C13 2.6p, L1 2.0nH 500mA, C14 3.0p, C15 100n, C16 10u |
| 48 MHz crystal | Y1, L2 24nH (XTAL_P series), C27 10p, C28 10p |
| USB Serial/JTAG series resistors | R3 22, R4 22 |
| CHIP_PU delay and reset | R7 10k, C17 1u, SW2 RESET |
| Boot strap (GPIO28) | R6 10k, SW1 BOOT |
| UART0 header | R5 499, J3 |
| Status LED (GPIO8) | R8 330, D1 |
| RF match, 2.4 GHz | C29_rf 2.0p, L3_rf 2.4nH, C30_rf 2.0p |
| RF match, 5 GHz | C31_rf 0.8p, L4_rf 1.5nH, C32_rf 0.8p |
| Diplexer | FL1_rf |
| Antenna CLC | C33_rf DNP, R18_rf 0, C34_rf DNP |
| Antenna connector | J5_rf U.FL |

## U5 TMC2240

| Function | Parts |
| --- | --- |
| VS decoupling | C21 100n 50V, C22 100n 50V |
| Charge pump | C23 1u 50V (VCP), C24 22n 50V (CPI-CPO) |
| VDD1V8 | C25 2.2u |
| VCC_IO | C26 100n |
| Current reference | R15 12k |
| DIAG0/DIAG1 pull-ups | R16 10k, R17 10k |
| Motor connector | J4 |

## U3 TLE5012B

| Function | Parts |
| --- | --- |
| Decoupling | C18 100n |
| SSC series resistors | R9 100 (SCK), R10 100 (CSQ), R11 470 (DATA) |

## U2 AP2112K-3.3

| Function | Parts |
| --- | --- |
| Input / output caps | C1 1u, C2 10u |

## Not tied to one chip

| Function | Parts |
| --- | --- |
| USB-C input, CC pull-downs | J1, R1 5.1k, R2 5.1k |
| Motor supply terminal and bulk (feeds U5) | J2, C19 100u 50V |
| VM_SENSE divider (feeds U1 GPIO1 ADC) | R12 100k, R13 10k, C20 100n |
