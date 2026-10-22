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
C1210 = "Capacitor_SMD:C_1210_3225Metric"
CP10 = "Capacitor_SMD:CP_Elec_10x10.5"

components: list[dict] = []
nets: dict[str, list[str]] = {}
groups: list[dict] = []


def part(ref, lib_id, value, footprint, unit=None, **fields):
    c = {"ref": ref, "lib_id": lib_id, "value": value, "footprint": footprint}
    if unit is not None:
        c["unit"] = unit
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

# ---------------------------------------------------------------- RP2354A core
# RP2354A: RP2350A die with 2 MB flash stacked in the package on the QSPI
# bus, so no external flash. The other QSPI pins are left open.
part(
    "U1", "MCU_RaspberryPi:RP2354A", "RP2354A",
    "Package_DFN_QFN:QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm",
    MPN="SC1511-A4", Manufacturer="Raspberry Pi",
)
res("R3", "27")
res("R4", "27")
connect("USB_C_DP", "R3.1")
connect("USB_C_DM", "R4.1")
connect("USB_DP", "R3.2", "U1.52")
connect("USB_DM", "R4.2", "U1.51")

iovdd = ["U1.1", "U1.11", "U1.20", "U1.30", "U1.38", "U1.45"]
decoup = []
for i, pin in enumerate(iovdd):
    decoup.append(cap(f"C{3 + i}", "100n"))
cap("C9", "100n")    # USB_OTP_VDD and QSPI_IOVDD share one, as on the reference design
cap("C10", "100n")   # ADC_AVDD
connect("+3V3", *iovdd, "U1.53", "U1.54", "U1.44",
        *(f"{c}.1" for c in decoup), "C9.1", "C10.1")
connect("GND", "U1.61", *(f"{c}.2" for c in decoup), "C9.2", "C10.2")

# Core switching regulator (RP2350 data sheet section 6.3.8): CIN and COUT
# 4.7u, fully shielded polarity-marked 3.3u inductor with its dot on the
# VOUT side, VREG_AVDD through a 33R / 4.7u filter. A second 4.7u sits on
# DVDD pin 23, the other DVDD pins get 100n.
part(
    "L1", "Device:L", "3.3u", "pico-step:L_Abracon_AOTA-B201610",
    MPN="AOTA-B201610S3R3-101-T", Manufacturer="Abracon",
)
cap("C11", "4.7u")   # CIN, VREG_VIN
cap("C12", "4.7u")   # COUT
res("R27", "33")
cap("C17", "4.7u")   # VREG_AVDD filter
cap("C13", "100n")   # DVDD pin 6
cap("C14", "100n")   # DVDD pin 39
cap("C36", "4.7u")   # DVDD pin 23
connect("+3V3", "U1.49", "C11.1", "R27.1")
connect("VREG_AVDD", "R27.2", "U1.46", "C17.1")
connect("VREG_LX", "U1.48", "L1.2")
connect("+1V1", "L1.1", "C12.1", "U1.50", "U1.6", "U1.23", "U1.39",
        "C13.1", "C14.1", "C36.1")
connect("GND", "U1.47", "C11.2", "C12.2", "C17.2", "C13.2", "C14.2", "C36.2")

# 12 MHz crystal: ABM8-272-T3 (CL 10 pF), 15 pF loads, 1k on XOUT.
part(
    "Y1", "Device:Crystal_GND24", "12MHz",
    "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    MPN="ABM8-272-T3", Manufacturer="Abracon",
)
cap("C15", "15p")
cap("C16", "15p")
res("R5", "1k")
connect("XIN", "U1.21", "Y1.1", "C15.1")
connect("XOUT", "U1.22", "R5.1")
connect("XTAL_OUT", "R5.2", "Y1.3", "C16.1")
connect("GND", "Y1.2", "Y1.4", "C15.2", "C16.2")

connect("QSPI_SS", "U1.60")

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
    ["R6", "SW1", "R7", "SW2", "J3", "R8", "D1"],
]})
groups.append({"name": "decoupling", "members": [
    *decoup, "C9", "C10", "C13", "C14", "C36",
]})
groups.append({"name": "core_regulator", "stages": [
    ["C11", "R27", "C17"], ["L1"], ["C12"],
]})

# ---------------------------------------------------------------- TLE5012B
# SSC per data sheet Figure 11: 100R on SCK and CSQ, 470R on DATA. The
# RP2354A SPI TX cannot tri-state, so it joins the DATA node through 4.7k
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
connect("ENC_SCK", "U1.14", "R9.1")       # GPIO10 SPI1 SCK
connect("ENC_SCK_S", "R9.2", "U3.2")
connect("ENC_CSQ", "U1.17", "R10.1")      # GPIO13 SPI1 CSn
connect("ENC_CSQ_S", "R10.2", "U3.3")
connect("ENC_TX", "U1.15", "R14.1")       # GPIO11 SPI1 TX
connect("ENC_DATA", "U1.16", "R14.2", "R11.1")  # GPIO12 SPI1 RX
connect("ENC_DATA_S", "R11.2", "U3.4")
connect("ENC_IFA", "U1.18", "U3.5")       # GPIO14, PWM output in E5000
connect("ENC_IFB", "U1.19", "U3.8")       # GPIO15
connect("ENC_IFC", "U1.27", "U3.1")       # GPIO16

groups.append({"name": "encoder", "stages": [
    ["R9", "R10", "R14", "R11"], ["U3", "C18"],
]})

# ---------------------------------------------------------------- motor supply
# VM runs up to 48 V. The sense divider puts 48 V at 2.55 V and reaches the
# 3.3 V ADC limit at 62 V, about the 63 V rating of the bulk capacitors.
part(
    "J2", "Connector:Screw_Terminal_01x02", "VM",
    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
)
part("C19", "Device:C_Polarized", "100u 63V", CP10)
res("R12", "100k")
res("R13", "5.6k")
cap("C20", "100n")
connect("VM", "J2.1", "C19.1", "R12.1")
connect("GND", "J2.2", "C19.2", "R13.2", "C20.2")
connect("VM_SENSE", "R12.2", "R13.1", "C20.1", "U1.40")  # GPIO26 ADC0

groups.append({"name": "motor_supply", "stages": [["J2"], ["C19"], ["R12", "R13", "C20"]]})

# ---------------------------------------------------------------- TMC5241
# Motion controller and driver with integrated 65 V bridges and current
# sensing, per the TMC5241 data sheet Figure 50 (Standard Application
# Circuit). 2 A RMS per coil at 24 V, 1.7 A RMS at 48 V.
#
# R15 (RREF) sets the full-scale current: 12k is the smallest allowed and
# gives 2.05 A RMS with DRV_CONF current range 2 or 3 (KIFS 36 A x kOhm,
# Table 17); firmware trims it with GLOBALSCALER/IRUN. The power-on default
# range 0 gives 0.67 A RMS.
#
# The charge pump capacitor CPI-CPO swings over the whole supply, so it is
# rated 100 V instead of the data sheet's 50 V. The VCP capacitor to VS sees
# only the 2.7 V the pump adds.
#
# The four VS pins are one net. As on ADI's TMC5241-EVKIT, the ceramics
# go in pairs at the two ends of the VS/OUT pin row.
part("U5", "pico-step:TMC5241", "TMC5241",
     "pico-step:ADI_TQFN-38-1EP_5x7mm_P0.5mm_EP3.65x5.6mm_ThermalVias",
     MPN="TMC5241ATU+T", Manufacturer="Analog Devices")
cap("C21", "100n 100V")         # VS, pin 30 end
cap("C22", "100n 100V")         # VS, pin 21 end
cap("C23", "1u 25V")            # VCP to VS
cap("C24", "22n 100V")          # CPI to CPO
cap("C25", "2.2u")              # VDD1V8
cap("C26", "100n")              # VCC_IO
cap("C33", "2.2u 100V", C1210)  # VS, pin 30 end
cap("C34", "2.2u 100V", C1210)  # VS, pin 21 end
part("C35", "Device:C_Polarized", "100u 63V", CP10)
res("R15", "12k")               # RREF, 1%
res("R16", "10k")
res("R17", "10k")
res("R24", "10k")
res("R25", "10k")
part("J4", "Connector_Generic:Conn_01x04", "Motor",
     "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical")

connect("VM", "U5.30", "U5.26", "U5.25", "U5.21", "C21.1", "C22.1", "C23.1",
        "C33.1", "C34.1", "C35.1")
connect("TMC_VCP", "U5.18", "C23.2")
connect("TMC_CPI", "U5.16", "C24.1")
connect("TMC_CPO", "U5.17", "C24.2")
connect("TMC_1V8", "U5.5", "C25.1")
connect("TMC_IREF", "U5.3", "R15.1")
connect("+3V3", "U5.7", "C26.1", "R16.1", "R17.1", "R24.1")
# UART_EN and CLK low: SPI, internal clock. AIN (0..1.25 V) is unused. The
# N.C. pins go to GND for cooling, as the data sheet allows.
connect("GND", "U5.6", "U5.23", "U5.28", "U5.39", "U5.12", "U5.38", "U5.4",
        "U5.19", "U5.20", "U5.31", "U5.32",
        "C21.2", "C22.2", "C25.2", "C26.2", "C33.2", "C34.2", "C35.2",
        "R15.2", "R25.2")
# Motor connector in the order 1A 2A 1B 2B.
connect("OUT1A", "U5.29", "J4.1")
connect("OUT2A", "U5.27", "J4.2")
connect("OUT1B", "U5.22", "J4.3")
connect("OUT2B", "U5.24", "J4.4")

# MCU interface: SPI0 on GPIO2..5.
connect("TMC_SCK", "U1.4", "U5.35")     # GPIO2 SPI0 SCK
connect("TMC_SDI", "U1.5", "U5.36")     # GPIO3 SPI0 TX
connect("TMC_SDO", "U1.7", "U5.37")     # GPIO4 SPI0 RX
connect("TMC_CSN", "U1.8", "U5.34")     # GPIO5 SPI0 CSn
# Reference switch inputs of the ramp generator, driven by the MCU (no
# STEP/DIR input on this part).
connect("TMC_REFL", "U1.9", "U5.1")     # GPIO6
connect("TMC_REFR", "U1.10", "U5.2")    # GPIO7
# DRV_ENN has an internal ~100k pull-up, which loses to the MCU's ~50k reset
# pull-down. 10k to 3V3 holds 2.75 V (VIH 0.7 x VCC_IO = 2.31 V): outputs
# stay off until firmware drives GPIO8 low.
connect("TMC_ENN", "U1.12", "U5.11", "R24.2")    # GPIO8
connect("TMC_DIAG0", "U1.13", "U5.13", "R16.2")  # GPIO9
connect("TMC_DIAG1", "U1.28", "U5.14", "R17.2")  # GPIO17
# nSLEEP low is sleep with every register cleared; a >30 us low pulse is a
# reset. The 10k pull-down keeps the driver asleep (bridges off, VS draw
# under 25 uA) until firmware raises GPIO18. The pin is VS rated with a
# 0.9 V input threshold, so 3.3 V drives it.
connect("TMC_SLEEPN", "U1.29", "U5.33", "R25.1")  # GPIO18
# The angle sensor's IIF outputs feed the encoder inputs, so firmware can
# switch the TLE5012B to IIF and let the TMC5241 count.
connect("ENC_IFA", "U5.10")
connect("ENC_IFB", "U5.9")
connect("ENC_IFC", "U5.8")

groups.append({"name": "driver", "stages": [
    ["R24", "R25", "R16", "R17"],
    ["U5"],
    ["R15", "C25", "C23", "C24"],
    ["J4"],
]})
groups.append({"name": "driver_supply", "stages": [
    ["C21", "C22", "C33", "C34", "C35"],
    ["C26"],
]})

unused_gpio = ["U1.2", "U1.3", "U1.31", "U1.32", "U1.33", "U1.34",
               "U1.35", "U1.36", "U1.41", "U1.42", "U1.43"]
# QSPI_SCLK, SD0..SD3: shared with the in-package flash, left open.
unused_qspi = ["U1.55", "U1.56", "U1.57", "U1.58", "U1.59"]

circuit = {
    "version": 1,
    "title": "pico-step",
    "components": components,
    "nets": [{"name": n, "pins": p} for n, p in nets.items()],
    "groups": groups,
    "power": {"VBUS": {"style": "label"}, "VM": {"style": "label"}},
    # OV (open drain, released above OVERVOLTAGE_VTH) is meant for a brake
    # chopper MOSFET; none is fitted.
    "no_connect": ["J1.A8", "J1.B8", "U2.4", "U5.15", *unused_gpio, *unused_qspi],
}

json.dump(circuit, sys.stdout, indent=1)
sys.stdout.write("\n")
