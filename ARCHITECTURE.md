# Architecture

```mermaid
classDiagram
    class USB_C_J1 {
        VBUS 5V
        D+ / D-
        CC1/CC2 5.1k pull-down
    }
    class LDO_U2 {
        AP2112K-3.3
        VBUS to +3V3
    }
    class ESP32_C5HF4_U1 {
        4 MB in-package flash
        48 MHz crystal Y1, 24 nH on XTAL_P
        CHIP_PU RC 10k/1u, RESET SW2
        BOOT SW1 on GPIO28
        USB Serial/JTAG GPIO13/14
        UART0 header J3
        LED GPIO8
    }
    class RF {
        CLC match per port
        diplexer FL1_rf LFD182G45DCHD481
        CLC footprint, U.FL J5_rf
    }
    class TMC2240_U5 {
        SPI shared bus, CSN GPIO10
        STEP GPIO9, DIR GPIO26
        ENN GPIO27, SLEEPN GPIO3
        DIAG0 GPIO24, DIAG1 GPIO25
        ENCA/B/N from TLE5012B IFA/IFB/IFC
        RREF 12k
    }
    class Motor_J4 {
        OUT1A OUT2A OUT1B OUT2B
    }
    class TLE5012B_U3 {
        SSC on shared SPI, 3-wire
        SCK GPIO6, DATA on MOSI GPIO7
        CSQ GPIO23
        IFA/IFB/IFC GPIO4/5/0
    }
    class MotorSupply_J2 {
        VM screw terminal
        100u bulk
        VM_SENSE divider to GPIO1 ADC1_CH0
    }
    USB_C_J1 --> LDO_U2 : VBUS
    USB_C_J1 --> ESP32_C5HF4_U1 : USB 22R series
    LDO_U2 --> ESP32_C5HF4_U1 : +3V3
    LDO_U2 --> TLE5012B_U3 : +3V3
    ESP32_C5HF4_U1 --> RF : ANT_2G / ANT_5G
    ESP32_C5HF4_U1 --> TMC2240_U5 : SPI + STEP/DIR
    TLE5012B_U3 --> ESP32_C5HF4_U1 : angle (SSC)
    MotorSupply_J2 --> TMC2240_U5 : VM
    TLE5012B_U3 --> TMC2240_U5 : IIF encoder
    TMC2240_U5 --> Motor_J4 : coils
    MotorSupply_J2 --> ESP32_C5HF4_U1 : VM_SENSE
```

## Power-up and boot

CHIP_PU rises through 10k into 1u (tau 10 ms) and enables the ESP32-C5 at
about 0.75 VDD. Strapping pins are latched within 3 ms after that. The
TMC2240 stays asleep (SLEEPN internal pull-down) with outputs off (DRV_ENN
internal pull-up) until firmware drives both.

```mermaid
gantt
    title Power-up sequence (ms, approximate)
    dateFormat x
    axisFormat %L
    section Rails
    +3V3 ramps (LDO soft start)         :r, 0, 1
    section ESP32-C5
    CHIP_PU RC charging, chip held off  :c, 0, 14
    Straps latched (GPIO25..28, 7, 2, 3):s, 14, 17
    ROM boot and firmware init          :b, 17, 60
    section TMC2240
    SLEEPN low, DRV_ENN high (off)      :t, 0, 60
    Configured over SPI, then enabled   :e, 60, 70
```
