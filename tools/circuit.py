#!/usr/bin/env python3
"""Build the kicad-vis circuit description for the pico-step board.

This file is the single source of truth for the schematic: parts, nets
and grouping. Run from the project root:
    python3 tools/circuit.py > build/circuit.json
"""

from __future__ import annotations

import json
import sys

R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"

components: list[dict] = []
nets: dict[str, list[str]] = {}
groups: list[dict] = []


def part(ref, lib_id, value, footprint, dnp=False, **fields):
    c = {"ref": ref, "lib_id": lib_id, "value": value, "footprint": footprint}
    if dnp:
        c["dnp"] = True
    if fields:
        c["fields"] = fields
    components.append(c)
    return ref


def res(ref, value):
    return part(ref, "Device:R", value, R0603)


def cap(ref, value, footprint=C0603):
    return part(ref, "Device:C", value, footprint)


def connect(net, *pins):
    nets.setdefault(net, []).extend(pins)


# ---------------------------------------------------------------- USB + 3V3
part(
    "J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C",
    "pico-step:USB_C_Receptacle_GCT_USB4105-xx-A_16P_SH",
    MPN="USB4105-GF-A", Manufacturer="GCT",
)
res("R1", "5.1k")
res("R2", "5.1k")
cap("C1", "1u")
part(
    "U2", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3",
    "Package_TO_SOT_SMD:SOT-23-5",
    MPN="AP2112K-3.3TRG1", Manufacturer="Diodes Incorporated",
)
cap("C2", "10u", C0805)

connect("VBUS", "J1.A4", "J1.A9", "J1.B4", "J1.B9", "C1.1", "U2.1", "U2.3")
connect("USB_CC1", "J1.A5", "R1.1")
connect("USB_CC2", "J1.B5", "R2.1")
connect("USB_C_DP", "J1.A6", "J1.B6")
connect("USB_C_DM", "J1.A7", "J1.B7")
connect("GND", "J1.A1", "J1.A12", "J1.B1", "J1.B12", "J1.SH",
        "R1.2", "R2.2", "C1.2", "U2.2", "C2.2")
connect("+3V3", "U2.5", "C2.1")

groups.append({"name": "usb_power", "stages": [["J1"], ["R1", "R2", "C1"], ["U2"], ["C2"]]})

# ---------------------------------------------------------------- ESP32-C5 core
# Support parts follow the ESP32-C5 Hardware Design Guidelines reference
# schematic (Fig. 1). The HF4 carries 4 MB flash in the package, so there is
# no external flash and pins 26..32 are NC.
C0201 = "Capacitor_SMD:C_0201_0603Metric"
L0201 = "Inductor_SMD:L_0201_0603Metric"
L0402 = "Inductor_SMD:L_0402_1005Metric"


def ind(ref, value, footprint=L0201):
    return part(ref, "Device:L", value, footprint)


part(
    "U1", "pico-step:ESP32-C5HF4", "ESP32-C5HF4",
    "Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.66x4.66mm_ThermalVias",
    MPN="ESP32-C5HF4", Manufacturer="Espressif Systems",
)

# USB Serial/JTAG on GPIO13 (D-) / GPIO14 (D+), 22R series per the guidelines.
res("R3", "22")
res("R4", "22")
connect("USB_C_DP", "R3.1")
connect("USB_C_DM", "R4.1")
connect("USB_DP", "R3.2", "U1.23")
connect("USB_DM", "R4.2", "U1.22")

# Supply decoupling, one entry per pin group as in the reference schematic.
cap("C3", "10u", C0805)   # VDDA6/VDDA7 (TX current step)
cap("C4", "0.8p", C0201)  # VDDA6/VDDA7 RF bypass
cap("C5", "0.3p", C0201)  # VDDA6/VDDA7 RF bypass
cap("C6", "1u")           # VDDA8
cap("C7", "1u")           # VDDPST1
cap("C8", "100n")         # VDDPST2
cap("C9", "1u")           # VDDA5
cap("C10", "10n")         # VDDA3/VDDA4
cap("C11", "100n")        # VDDA3/VDDA4
cap("C12", "100n")        # VDDPST3
# VDDA1/VDDA2 get an LC filter against PA harmonics; the inductor must
# carry the RF supply current (500 mA rating).
cap("C13", "2.6p", C0201)  # chip side of L1
ind("L1", "2.0nH 500mA")
cap("C14", "3.0p", C0201)
cap("C15", "100n")
cap("C16", "10u", C0805)
decoup = [f"C{n}" for n in range(3, 17)]
connect("+3V3", "U1.1", "U1.3", "U1.6", "U1.8", "U1.24", "U1.46",
        "U1.44", "U1.45", "U1.39", "L1.2",
        *(f"{c}.1" for c in decoup if c != "C13"))
connect("VDDA12", "U1.40", "U1.41", "C13.1", "L1.1")
connect("GND", "U1.2", "U1.43", "U1.47", "U1.49", *(f"{c}.2" for c in decoup))

# 48 MHz crystal (the only frequency the firmware supports), +-10 ppm.
# FL4800069: CL 8 pF, so 10 pF loads with ~3 pF stray; trim after a
# frequency-offset test. The series inductor on XTAL_P keeps crystal
# harmonics out of the RF band (24 nH initial value per the guidelines).
part(
    "Y1", "Device:Crystal_GND24", "48MHz",
    "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    MPN="FL4800069", Manufacturer="Diodes Incorporated",
)
ind("L2", "24nH", L0402)
cap("C27", "10p")
cap("C28", "10p")
connect("XTAL_P", "U1.5", "L2.1")
connect("XTAL_IN", "L2.2", "Y1.1", "C27.1")
connect("XTAL_N", "U1.4", "Y1.3", "C28.1")
connect("GND", "Y1.2", "Y1.4", "C27.2", "C28.2")

# CHIP_PU: 10k / 1u delays enable until the 3V3 rail settles (tSTBL); RESET
# shorts the capacitor. BOOT holds GPIO28 low through reset for download
# mode; GPIO27 must read high then, which its internal pull-up and the
# TMC2240 DRV_ENN pull-up guarantee.
SW = "Button_Switch_SMD:SW_SPST_PTS810"
res("R7", "10k")
cap("C17", "1u")
part("SW2", "Switch:SW_Push", "RESET", SW)
res("R6", "10k")
part("SW1", "Switch:SW_Push", "BOOT", SW)
connect("CHIP_PU", "U1.7", "R7.2", "C17.1", "SW2.1")
connect("BOOT", "U1.38", "R6.2", "SW1.1")    # GPIO28
connect("+3V3", "R7.1", "R6.1")
connect("GND", "C17.2", "SW1.2", "SW2.2")

# UART0 header for ROM log and download; 499R on U0TXD suppresses harmonics.
res("R5", "499")
part("J3", "Connector_Generic:Conn_01x03", "UART",
     "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical")
connect("U0TXD", "U1.20", "R5.1")
connect("UART_TX", "R5.2", "J3.1")
connect("GND", "J3.2")
connect("UART_RX", "U1.21", "J3.3")

# Status LED on GPIO8.
res("R8", "330")
part("D1", "Device:LED", "LED", "LED_SMD:LED_0603_1608Metric")
connect("LED", "U1.17", "R8.1")
connect("LED_A", "R8.2", "D1.2")
connect("GND", "D1.1")

groups.append({"name": "mcu", "stages": [
    ["R3", "R4"],
    ["Y1", "C27", "C28"],
    ["L2"],
    ["U1"],
    ["R7", "C17", "SW2", "R6", "SW1", "R5", "J3", "R8", "D1"],
]})
groups.append({"name": "decoupling", "members": [*decoup, "L1"]})

# ---------------------------------------------------------------- RF
# Per the guidelines: a CLC match at each chip RF port, a dual-band diplexer
# to one 50 ohm port, and a CLC footprint at the antenna. Chip-side values
# are mid-range starting points from the guidelines' recommended ranges
# (2.4 GHz: 1.2..3.0 pF / 2.0..3.0 nH, 5 GHz: 0.2..1.5 pF / 0..3 nH); all
# of them must be tuned on the finished board with a network analyzer.
part("FL1", "pico-step:LFD182G45DCHD481", "LFD182G45DCHD481",
     "pico-step:Murata_LFD182G45DCHD481",
     MPN="LFD182G45DCHD481", Manufacturer="Murata Electronics")
cap("C29", "2.0p", C0201)
ind("L3", "2.4nH")
cap("C30", "2.0p", C0201)
cap("C31", "0.8p", C0201)   # needs a short stub to the ground pad
ind("L4", "1.5nH")
cap("C32", "0.8p", C0201)
part("C33", "Device:C", "DNP", C0201, dnp=True)
part("R18", "Device:R", "0", "Resistor_SMD:R_0201_0603Metric")
part("C34", "Device:C", "DNP", C0201, dnp=True)
part("J5", "Connector:Conn_Coaxial", "ANT",
     "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
     MPN="U.FL-R-SMT-1(10)", Manufacturer="Hirose")
connect("ANT_2G", "U1.42", "C29.1", "L3.1")
connect("RF_2G", "L3.2", "C30.1", "FL1.3")
connect("ANT_5G", "U1.48", "C31.1", "L4.1")
connect("RF_5G", "L4.2", "C32.1", "FL1.1")
connect("RF_COM", "FL1.6", "C33.1", "R18.1")
connect("RF_ANT", "R18.2", "C34.1", "J5.1")
connect("GND", "FL1.2", "FL1.5", "FL1.7", "J5.2",
        "C29.2", "C30.2", "C31.2", "C32.2", "C33.2", "C34.2")

groups.append({"name": "rf", "stages": [
    ["C29", "C31"], ["L3", "L4"], ["C30", "C32"], ["FL1"],
    ["C33"], ["R18"], ["C34"], ["J5"],
]})

# ---------------------------------------------------------------- TLE5012B
# SSC per data sheet Figure 11: 100R on SCK and CSQ, 470R on DATA. The
# sensor shares the SPI bus with the TMC2240 (the ESP32-C5 has one general
# purpose SPI host). DATA sits on MOSI: in 3-wire half-duplex mode the SPI
# host tri-states MOSI for the read phase, which is the bidirectional
# master Figure 11 asks for. Both slaves release their outputs while
# deselected.
part(
    "U3", "Sensor_Magnetic:TLE5012B", "TLE5012BE5000",
    "pico-step:Infineon_PG-DSO-8",
    MPN="TLE5012BE5000XUMA1", Manufacturer="Infineon",
)
cap("C18", "100n")
res("R9", "100")
res("R10", "100")
res("R11", "470")
connect("+3V3", "U3.6", "C18.1")
connect("GND", "U3.7", "C18.2")
connect("SPI_SCK", "U1.15", "R9.1")       # GPIO6, FSPICLK
connect("ENC_SCK_S", "R9.2", "U3.2")
connect("ENC_CSQ", "U1.33", "R10.1")      # GPIO23
connect("ENC_CSQ_S", "R10.2", "U3.3")
connect("SPI_MOSI", "U1.16", "R11.1")     # GPIO7, FSPID
connect("ENC_DATA_S", "R11.2", "U3.4")
connect("ENC_IFA", "U1.13", "U3.5")       # GPIO4, PWM output in E5000
connect("ENC_IFB", "U1.14", "U3.8")       # GPIO5
connect("ENC_IFC", "U1.9", "U3.1")        # GPIO0

groups.append({"name": "encoder", "stages": [
    ["R9", "R10", "R11"], ["U3", "C18"],
]})

# ---------------------------------------------------------------- motor supply
part(
    "J2", "Connector:Screw_Terminal_01x02", "VM",
    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
)
part("C19", "Device:C_Polarized", "100u 50V", "Capacitor_SMD:CP_Elec_10x10.5")
res("R12", "100k")
res("R13", "10k")
cap("C20", "100n")
connect("VM", "J2.1", "C19.1", "R12.1")
connect("GND", "J2.2", "C19.2", "R13.2", "C20.2")
connect("VM_SENSE", "R12.2", "R13.1", "C20.1", "U1.10")  # GPIO1 ADC1_CH0

groups.append({"name": "motor_supply", "stages": [["J2"], ["C19"], ["R12", "R13", "C20"]]})

# ---------------------------------------------------------------- TMC2240
# Support parts per TMC2240 data sheet Figure 35 (Standard Application
# Circuit): 100n at each VS pin pair, 1u VCP to VS, 22n 50V CPI-CPO, 2.2u on
# VDD1V8, 100n on VCC_IO. RREF 12k gives the widest full-scale range
# (2.12 A RMS at DRV_CONF=11, Table 18); firmware scales current down.
C50V = "Capacitor_SMD:C_0603_1608Metric"
part("U5", "pico-step:TMC2240", "TMC2240", "pico-step:Maxim_TQFN-32-1EP_5x5mm_P0.5mm_T3255-5",
     MPN="TMC2240ATJ+T", Manufacturer="Analog Devices")
cap("C21", "100n 50V", C50V)
cap("C22", "100n 50V", C50V)
cap("C23", "1u 50V", C0805)
cap("C24", "22n 50V", C50V)
cap("C25", "2.2u")
cap("C26", "100n")
res("R15", "12k")
res("R16", "10k")
res("R17", "10k")
part("J4", "Connector_Generic:Conn_01x04", "Motor",
     "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical")

connect("VM", "U5.17", "U5.20", "U5.21", "U5.24", "C21.1", "C22.1", "C23.1")
connect("TMC_VCP", "U5.16", "C23.2")
connect("TMC_CPI", "U5.14", "C24.1")
connect("TMC_CPO", "U5.15", "C24.2")
connect("TMC_1V8", "U5.3", "C25.1")
connect("TMC_IREF", "U5.1", "R15.1")
connect("+3V3", "U5.5", "C26.1", "R16.1", "R17.1")
# AIN unused (0..1.25 V input); CLK low selects the internal clock;
# UART_EN low selects SPI.
connect("GND", "U5.4", "U5.33", "U5.2", "U5.30", "U5.10",
        "C21.2", "C22.2", "C25.2", "C26.2", "R15.2")
connect("OUT1A", "U5.23", "J4.1")
connect("OUT2A", "U5.22", "J4.2")
connect("OUT1B", "U5.18", "J4.3")
connect("OUT2B", "U5.19", "J4.4")

# ESP32-C5 interface: SPI bus shared with the TLE5012B.
connect("SPI_SCK", "U5.27")
connect("SPI_MOSI", "U5.28")
connect("SPI_MISO", "U1.11", "U5.29")   # GPIO2, FSPIQ
connect("TMC_CSN", "U1.19", "U5.26")    # GPIO10, FSPICS0
connect("TMC_STEP", "U1.18", "U5.31")   # GPIO9
# GPIO26 is a boot-mode strap, but it only matters when GPIO27 is low.
connect("TMC_DIR", "U1.36", "U5.32")    # GPIO26
# DRV_ENN has an internal pull-up, so outputs stay off until firmware drives
# GPIO27 low; the same pull-up holds the GPIO27 strap high for download mode.
connect("TMC_ENN", "U1.37", "U5.9")     # GPIO27
# DIAG0 is pulled low while the driver is in reset, so it stays off the
# boot-mode strapping pins.
connect("TMC_DIAG0", "U1.34", "U5.11", "R16.2")  # GPIO24
connect("TMC_DIAG1", "U1.35", "U5.12", "R17.2")  # GPIO25
# SLEEPN has an internal pull-down, so the driver sleeps until firmware
# raises GPIO3.
connect("TMC_SLEEPN", "U1.12", "U5.25")  # GPIO3
# The angle sensor's IIF outputs also feed the driver's encoder inputs, so
# firmware can switch the TLE5012B to IIF and let the TMC2240 count.
connect("ENC_IFA", "U5.8")
connect("ENC_IFB", "U5.7")
connect("ENC_IFC", "U5.6")

groups.append({"name": "driver", "stages": [
    ["R16", "R17", "C26"], ["U5"], ["C21", "C22", "C23", "C24", "C25", "R15"], ["J4"],
]})

# GPIO15 (SPICS1) is the in-package PSRAM select on other variants; the data
# sheet advises against general use. Pins 26..32 are NC on the HF4.
unused_mcu = ["U1.25", *(f"U1.{n}" for n in range(26, 33))]

circuit = {
    "version": 1,
    "title": "pico-step",
    "components": components,
    "nets": [{"name": n, "pins": p} for n, p in nets.items()],
    "groups": groups,
    "power": {"VBUS": {"style": "label"}, "VM": {"style": "label"},
              "VDDA12": {"style": "label"}},
    "no_connect": ["J1.A8", "J1.B8", "U2.4", "U5.13", *unused_mcu],
}

json.dump(circuit, sys.stdout, indent=1)
sys.stdout.write("\n")
