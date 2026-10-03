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


def part(ref, lib_id, value, footprint, **fields):
    c = {"ref": ref, "lib_id": lib_id, "value": value, "footprint": footprint}
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

# ---------------------------------------------------------------- RP2040 core
part(
    "U1", "MCU_RaspberryPi:RP2040", "RP2040",
    "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm",
    MPN="SC0914(13)", Manufacturer="Raspberry Pi",
)
res("R3", "27")
res("R4", "27")
connect("USB_C_DP", "R3.1")
connect("USB_C_DM", "R4.1")
connect("USB_DP", "R3.2", "U1.47")
connect("USB_DM", "R4.2", "U1.46")

iovdd = ["U1.1", "U1.10", "U1.22", "U1.33", "U1.42", "U1.49"]
decoup = []
for i, pin in enumerate(iovdd):
    decoup.append(cap(f"C{3 + i}", "100n"))
cap("C9", "100n")    # USB_VDD
cap("C10", "100n")   # ADC_AVDD
cap("C11", "1u")     # VREG_VIN
cap("C12", "1u")     # VREG_VOUT
cap("C13", "100n")   # DVDD pin 23
cap("C14", "100n")   # DVDD pin 50
connect("+3V3", *iovdd, "U1.48", "U1.43", "U1.44",
        *(f"{c}.1" for c in decoup), "C9.1", "C10.1", "C11.1")
connect("+1V1", "U1.45", "U1.23", "U1.50", "C12.1", "C13.1", "C14.1")
connect("GND", "U1.57", "U1.19",
        *(f"{c}.2" for c in decoup), "C9.2", "C10.2", "C11.2",
        "C12.2", "C13.2", "C14.2")

# 12 MHz crystal: ABM8-272-T3 (CL 10 pF), 15 pF loads, 1k on XOUT.
part(
    "Y1", "Device:Crystal_GND24", "12MHz",
    "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    MPN="ABM8-272-T3", Manufacturer="Abracon",
)
cap("C15", "15p")
cap("C16", "15p")
res("R5", "1k")
connect("XIN", "U1.20", "Y1.1", "C15.1")
connect("XOUT", "U1.21", "R5.1")
connect("XTAL_OUT", "R5.2", "Y1.3", "C16.1")
connect("GND", "Y1.2", "Y1.4", "C15.2", "C16.2")

# QSPI flash
part(
    "U4", "Memory_Flash:W25Q128JVS", "W25Q128JVS",
    "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm",
    MPN="W25Q128JVSIQ", Manufacturer="Winbond",
)
cap("C17", "100n")
connect("QSPI_SS", "U1.56", "U4.1")
connect("QSPI_SCLK", "U1.52", "U4.6")
connect("QSPI_SD0", "U1.53", "U4.5")
connect("QSPI_SD1", "U1.55", "U4.2")
connect("QSPI_SD2", "U1.54", "U4.3")
connect("QSPI_SD3", "U1.51", "U4.7")
connect("+3V3", "U4.8", "C17.1")
connect("GND", "U4.4", "C17.2")

# BOOTSEL pulls QSPI_SS low through 1k; RESET pulls RUN low.
SW = "Button_Switch_SMD:SW_SPST_PTS810"
res("R6", "1k")
part("SW1", "Switch:SW_Push", "BOOTSEL", SW)
res("R7", "10k")
part("SW2", "Switch:SW_Push", "RESET", SW)
connect("QSPI_SS", "R6.1")
connect("BOOTSEL", "R6.2", "SW1.1")
connect("RUN", "U1.26", "R7.2", "SW2.1")
connect("+3V3", "R7.1")
connect("GND", "SW1.2", "SW2.2")

# SWD header
part("J3", "Connector_Generic:Conn_01x03", "SWD",
     "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical")
connect("SWCLK", "U1.24", "J3.1")
connect("GND", "J3.2")
connect("SWDIO", "U1.25", "J3.3")

# Status LED on GPIO25
res("R8", "330")
part("D1", "Device:LED", "LED", "LED_SMD:LED_0603_1608Metric")
connect("LED", "U1.37", "R8.1")
connect("LED_A", "R8.2", "D1.2")
connect("GND", "D1.1")

groups.append({"name": "mcu", "stages": [
    ["R3", "R4"],
    ["Y1", "C15", "C16", "R5"],
    ["U1"],
    ["U4", "C17", "R6", "SW1", "R7", "SW2", "J3", "R8", "D1"],
]})
groups.append({"name": "decoupling", "members": [
    *decoup, "C9", "C10", "C11", "C12", "C13", "C14",
]})

# ---------------------------------------------------------------- TLE5012B
# SSC per data sheet Figure 11: 100R on SCK and CSQ, 470R on DATA. The
# RP2040 SPI TX cannot tri-state, so it joins the DATA node through 4.7k
# and loses any contention with the sensor; RX reads the node directly.
part(
    "U3", "Sensor_Magnetic:TLE5012B", "TLE5012BE5000",
    "pico-step:Infineon_PG-DSO-8",
    MPN="TLE5012BE5000XUMA1", Manufacturer="Infineon",
)
cap("C18", "100n")
res("R9", "100")
res("R10", "100")
res("R11", "470")
res("R14", "4.7k")
connect("+3V3", "U3.6", "C18.1")
connect("GND", "U3.7", "C18.2")
connect("ENC_SCK", "U1.13", "R9.1")       # GPIO10 SPI1 SCK
connect("ENC_SCK_S", "R9.2", "U3.2")
connect("ENC_CSQ", "U1.16", "R10.1")      # GPIO13 SPI1 CSn
connect("ENC_CSQ_S", "R10.2", "U3.3")
connect("ENC_TX", "U1.14", "R14.1")       # GPIO11 SPI1 TX
connect("ENC_DATA", "U1.15", "R14.2", "R11.1")  # GPIO12 SPI1 RX
connect("ENC_DATA_S", "R11.2", "U3.4")
connect("ENC_IFA", "U1.17", "U3.5")       # GPIO14, PWM output in E5000
connect("ENC_IFB", "U1.18", "U3.8")       # GPIO15
connect("ENC_IFC", "U1.27", "U3.1")       # GPIO16

groups.append({"name": "encoder", "stages": [
    ["R9", "R10", "R14", "R11"], ["U3", "C18"],
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
connect("VM_SENSE", "R12.2", "R13.1", "C20.1", "U1.38")  # GPIO26 ADC0

groups.append({"name": "motor_supply", "stages": [["J2"], ["C19"], ["R12", "R13", "C20"]]})

# ---------------------------------------------------------------- TMC2240 I/O
# RP2040 side of the driver interface. SPI0 on GPIO2..5.
TMC_IO = {
    "TMC_SCK": "U1.4",     # GPIO2 SPI0 SCK
    "TMC_SDI": "U1.5",     # GPIO3 SPI0 TX
    "TMC_SDO": "U1.6",     # GPIO4 SPI0 RX
    "TMC_CSN": "U1.7",     # GPIO5 SPI0 CSn
    "TMC_STEP": "U1.8",    # GPIO6
    "TMC_DIR": "U1.9",     # GPIO7
    "TMC_ENN": "U1.11",    # GPIO8
    "TMC_DIAG0": "U1.12",  # GPIO9
    "TMC_DIAG1": "U1.28",  # GPIO17
}
for net, pin in TMC_IO.items():
    connect(net, pin)

unused_gpio = ["U1.2", "U1.3", "U1.29", "U1.30", "U1.31", "U1.32", "U1.34",
               "U1.35", "U1.36", "U1.39", "U1.40", "U1.41"]

circuit = {
    "version": 1,
    "title": "pico-step",
    "components": components,
    "nets": [{"name": n, "pins": p} for n, p in nets.items()],
    "groups": groups,
    "power": {"VBUS": {"style": "label"}, "VM": {"style": "label"}},
    "no_connect": ["J1.A8", "J1.B8", "U2.4", *unused_gpio],
}

json.dump(circuit, sys.stdout, indent=1)
sys.stdout.write("\n")
