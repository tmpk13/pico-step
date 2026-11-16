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

## Q3. In which order do the boards stack, from the motor up?
Why it matters: it picks each board's J5 and J6 parts (pins, socket or
stacking socket) for the DigiKey list. The encoder board sits next to the
shaft magnet in every order.
- A. Encoder, driver, mcu (recommended): the motor leads and the 48 V
  input stay low, near the motor; USB-C, the buttons and the LED stay on
  top, within reach.
- B. Encoder, mcu, driver: the TMC5241 sheds heat into open air on top,
  but USB-C ends up in the middle of the stack.
Applied: not yet; no header parts are chosen, so nothing depends on it.
Answer:
