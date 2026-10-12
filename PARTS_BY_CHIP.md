# Parts by chip

Every one of the 84 parts on the board, grouped by the chip it supports.

## U1 RP2354A

| Function | Parts |
| --- | --- |
| Decoupling, IOVDD | C3..C8 100n |
| Decoupling, USB_OTP_VDD + QSPI_IOVDD / ADC_AVDD | C9 100n, C10 100n |
| Core regulator, CIN / COUT / inductor | C11 4.7u, C12 4.7u, L1 3.3u |
| Core regulator, VREG_AVDD filter | R27 33, C17 4.7u |
| Decoupling, DVDD (pins 6, 39, 23) | C13 100n, C14 100n, C36 4.7u |
| 12 MHz crystal | Y1, C15 15p, C16 15p, R5 1k (XOUT) |
| USB series resistors | R3 27, R4 27 |
| BOOTSEL and reset | R6 1k, SW1 BOOTSEL, R7 10k, SW2 RESET |
| SWD header | J3 |
| Status LED (GPIO25) | R8 330, D1 |

## U5 TMC5160A

| Function | Parts |
| --- | --- |
| Power bridges (A: Q1..Q4, B: Q5..Q8) | Q1..Q8 CSD19537Q3 |
| Bootstrap, CA1 CA2 CB1 CB2 | C29..C32 220n |
| Sense resistors, phase A / B | R15 0.1, R18 0.1 |
| Sense line filters, SRAH SRAL SRBH SRBL | R19..R22 47 |
| Bridge decoupling | C33 2.2u 100V, C34 2.2u 100V, C35 100u 63V |
| VS / VSA decoupling | C21 100n 100V, C22 100n 100V |
| Charge pump | C23 100n 100V (VCP), C24 22n 100V (CPI-CPO) |
| 12VOUT gate supply | C25 10u 25V |
| 5VOUT and VCC | C27 4.7u, R23 2.2, C28 470n |
| VCC_IO | C26 100n |
| DIAG0/DIAG1 pull-ups | R16 10k, R17 10k |
| DRV_ENN pull-up (off during MCU reset) | R24 10k |
| SD_MODE pull-down (motion controller mode) | R25 10k |
| ENCN series (contention guard) | R26 1k |
| Motor connector | J4 |

## U3 TLE5012B

| Function | Parts |
| --- | --- |
| Decoupling | C18 100n |
| SSC series resistors | R9 100 (SCK), R10 100 (CSQ), R11 470 (DATA) |
| SPI1 TX into DATA (TX cannot tri-state) | R14 4.7k |

## U2 AP2112K-3.3

| Function | Parts |
| --- | --- |
| Input / output caps | C1 1u, C2 10u |

## Not tied to one chip

| Function | Parts |
| --- | --- |
| USB-C input, CC pull-downs | J1, R1 5.1k, R2 5.1k |
| Motor supply terminal and bulk (feeds U5) | J2, C19 100u 63V |
| VM_SENSE divider (feeds U1 GPIO26 ADC0) | R12 100k, R13 5.6k, C20 100n |
