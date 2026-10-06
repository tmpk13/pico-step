# Parts by chip

Every one of the 56 parts on the board, grouped by the chip it supports.

## U1 RP2040

| Function | Parts |
| --- | --- |
| Decoupling, IOVDD | C3..C8 100n |
| Decoupling, USB_VDD / ADC_AVDD | C9 100n, C10 100n |
| Core regulator, VREG_VIN / VREG_VOUT | C11 1u, C12 1u |
| Decoupling, DVDD | C13 100n, C14 100n |
| 12 MHz crystal | Y1, C15 15p, C16 15p, R5 1k (XOUT) |
| QSPI flash | U4 W25Q128JVS, C17 100n |
| USB series resistors | R3 27, R4 27 |
| BOOTSEL and reset | R6 1k, SW1 BOOTSEL, R7 10k, SW2 RESET |
| SWD header | J3 |
| Status LED (GPIO25) | R8 330, D1 |

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
| SPI1 TX into DATA (TX cannot tri-state) | R14 4.7k |

## U2 AP2112K-3.3

| Function | Parts |
| --- | --- |
| Input / output caps | C1 1u, C2 10u |

## Not tied to one chip

| Function | Parts |
| --- | --- |
| USB-C input, CC pull-downs | J1, R1 5.1k, R2 5.1k |
| Motor supply terminal and bulk (feeds U5) | J2, C19 100u 50V |
| VM_SENSE divider (feeds U1 GPIO26 ADC0) | R12 100k, R13 10k, C20 100n |
