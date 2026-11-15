# Questions

## Q1. Which board gets each half of the old power sheet?
Why it matters: USB-C and the 3.3 V LDO serve the MCU; the VM terminal
carries up to 48 V at motor current, which a fine-pitch bus header should
not carry.
- A. Split (recommended): USB-C, AP2112K and C1/C2 on the mcu board; J2,
  C19 and the VM_SENSE divider on the driver board, so only the divided
  VM_SENSE crosses the stack.
- B. All on the mcu board: VM must cross J5 to the driver at motor current.
- C. All on the driver board: USB D+/D- and VBUS cross J5 to the MCU.
Applied: A, in 6056377.
Answer:

## Q2. What joins the stacked boards?
Why it matters: it fixes the pinout every board routes to and the board
area the connector takes on a 42 mm NEMA17 outline.
- A. One 2x12 2.54 mm bus (recommended): J5 with the same pinout on every
  board, so any stack order works and boards can also be cabled with IDC
  ribbon; 30.5 mm long.
- B. One 2x12 1.27 mm bus: the same pinout in 15.2 mm, but stacking parts
  are scarcer and harder to hand-solder.
- C. Two connectors (mcu-driver, mcu-encoder): fewer pins each, but the
  middle board must pass the other board's lines through, so the stack
  order is fixed.
Applied: A, in 6056377 (stack/stack.tsch). Still open with A: the stack order, which
picks each board's J5 part (pins, socket, or stacking socket) for the
DigiKey list.
Answer:
