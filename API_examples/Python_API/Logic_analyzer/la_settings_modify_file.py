#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - Decoder Settings Modification
==========================================================

This example demonstrates how to programmatically modify decoder settings for
UART, SPI, I2C, and CAN protocols and export them to JSON configuration files.
The script retrieves default settings from the Logic Analyzer, modifies them
according to your requirements, and saves them to individual JSON files that
can be used for protocol decoding.

Features:
- Retrieve default decoder settings for all protocols
- Modify decoder parameters programmatically
- Export settings to JSON configuration files
- Support for UART, SPI, I2C, and CAN decoders
- Template for creating custom decoder configurations
- Reusable settings files for consistent decoding

Use Cases:
- Create standard decoder configuration templates
- Save custom decoder settings for repeated use
- Share decoder configurations between projects
- Automate decoder setup with predefined parameters
- Document protocol-specific configurations

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- No physical connections required (settings only)

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Logic Analyzer module (rp_la)
- Logic Analyzer FPGA image must be loaded
- OS 2.00 or higher

Usage:
    python la_settings_modify_file.py
    
    The program will:
    1. Initialize Logic Analyzer controller
    2. Add decoders for UART, SPI, I2C, and CAN
    3. Retrieve default settings for each decoder
    4. Modify settings with custom parameters
    5. Save settings to JSON files:
       - settings_uart.json
       - settings_spi.json
       - settings_i2c.json
       - settings_can.json

Configuration:
    Modify the settings dictionaries in the script to customize:
    - UART: Baud rate, data bits, parity, stop bits, pin assignments
    - SPI: Mode (CPOL/CPHA), bit order, word size, pin assignments
    - I2C: Address format, pin assignments
    - CAN: Bitrates, sample point, pin assignment

Output Files:
    The script generates JSON files that can be loaded by decoder applications
    or used as configuration templates for future protocol analysis sessions.

Author: Red Pitaya
Date: January 2026
"""

import json
import rp_hw_profiles
import rp_la
from rp_overlay import overlay

# ==============================================================================
# CALLBACK CLASS - Handle Logic Analyzer events
# ==============================================================================

class Callback(rp_la.CLACallback):
    """Callback class for Logic Analyzer events"""
    
    def captureStatus(self, controller, isTimeout, bytes, samples, preTrig, postTrig):
        """Called when capture status changes"""
        print(f"CaptureStatus: timeout={isTimeout}, bytes={bytes}, samples={samples}, "
              f"preTrig={preTrig}, postTrig={postTrig}")

    def decodeDone(self, controller, name):
        """Called when decoding is complete"""
        print(f"Decode done: {name}")


# ==============================================================================
# CONFIGURATION - Decoder Names and Acquisition Settings
# ==============================================================================

print("=" * 70)
print("Red Pitaya Logic Analyzer - Decoder Settings Modification")
print("=" * 70)

# Decoder identifiers
can_decoder = "CAN"
uart_decoder = "UART"
spi_decoder = "SPI"
i2c_decoder = "I2C"

# Calculate acquisition rate based on decimation
decimation = 16
acq_rate = int(rp_hw_profiles.rp_HPGetBaseSpeedHzOrDefault() / decimation)

print("\nConfiguration:")
print(f"  Decimation:        {decimation}")
print(f"  Acquisition rate:  {acq_rate} Hz ({acq_rate/1e6:.2f} MHz)")


# ==============================================================================
# INITIALIZATION - Create Logic Analyzer Controller
# ==============================================================================

print("\n" + "=" * 70)
print("Initializing Logic Analyzer...")
print("=" * 70)

# Change FPGA image to Logic Analyzer
fpga = overlay("logic")
print("Logic Analyzer FPGA image loaded")

# Create controller
rp_cla = rp_la.CLAController()
print("Logic Analyzer controller created")

# Set callback for events
callback = Callback()
rp_cla.setDelegate(callback.__disown__())
print("Event callback registered")

# Initialize FPGA (LA FPGA must be loaded/LA Application must be open)
rp_cla.initFpga()
print("Logic Analyzer FPGA initialized")


# ==============================================================================
# DECODER SETUP - Add Protocol Decoders
# ==============================================================================

print("\n" + "=" * 70)
print("Adding Protocol Decoders...")
print("=" * 70)

# Add decoders for all protocols
rp_cla.addDecoder(uart_decoder, rp_la.LA_DECODER_UART)
print(f"Added {uart_decoder} decoder")

rp_cla.addDecoder(spi_decoder, rp_la.LA_DECODER_SPI)
print(f"Added {spi_decoder} decoder")

rp_cla.addDecoder(i2c_decoder, rp_la.LA_DECODER_I2C)
print(f"Added {i2c_decoder} decoder")

rp_cla.addDecoder(can_decoder, rp_la.LA_DECODER_CAN)
print(f"Added {can_decoder} decoder")


# ==============================================================================
# RETRIEVE SETTINGS - Get Default Decoder Settings
# ==============================================================================

print("\n" + "=" * 70)
print("Retrieving Default Decoder Settings...")
print("=" * 70)

# Get settings from Red Pitaya
settings_uart = rp_cla.getDecoderSettings(uart_decoder)
settings_spi = rp_cla.getDecoderSettings(spi_decoder)
settings_i2c = rp_cla.getDecoderSettings(i2c_decoder)
settings_can = rp_cla.getDecoderSettings(can_decoder)

print(f"\nDefault UART settings:\n{settings_uart}")
print(f"\nDefault SPI settings:\n{settings_spi}")
print(f"\nDefault I2C settings:\n{settings_i2c}")
print(f"\nDefault CAN settings:\n{settings_can}")


# ==============================================================================
# MODIFY SETTINGS - Parse JSON and Update Parameters
# ==============================================================================

print("\n" + "=" * 70)
print("Modifying Decoder Settings...")
print("=" * 70)

# Parse JSON strings to dictionaries
settings_uart = json.loads(settings_uart)
settings_spi = json.loads(settings_spi)
settings_i2c = json.loads(settings_i2c)
settings_can = json.loads(settings_can)


# UART Decoder Settings
# ----------------------
print("\nConfiguring UART decoder...")
settings_uart["acq_speed"    ] = acq_rate       # Acquisition speed (min 4x baud rate). Default: 1 MHz
settings_uart["baudrate"     ] = 921600         # Baud rate: 1200,2400,4800,9600,19200,38400,57600,115200,230400,576000,921600
settings_uart["bitOrder"     ] = "LsbFirst"     # Bit order: LsbFirst/MsbFirst
settings_uart["invert"       ] = "No"           # Bit inversion: No/Yes
settings_uart["num_data_bits"] = "Bits8"        # Data bits: Bits5-9
settings_uart["num_stop_bits"] = "Stop_Bit_No"  # Stop bits: Stop_Bit_No/05/10/15/20
settings_uart["parity"       ] = "None"         # Parity: None, Even, Odd, Always_0, Always_1
settings_uart["rx"           ] = "DIN1"         # UART RX pin: "DIN0" - "DIN7", "None" = disabled.
settings_uart["tx"           ] = "None"         # UART TX pin: "DIN0" - "DIN7", "None" = disabled.
print(f"  Baud rate:     {settings_uart['baudrate']} bps")
print(f"  Data bits:     {settings_uart['num_data_bits']}")
print(f"  Parity:        {settings_uart['parity']}")
print(f"  RX pin:        {settings_uart['rx']}" if settings_uart['rx'] else "  RX pin:        Disabled")


# SPI Decoder Settings
# --------------------
# SPI Modes:
# - Mode 0: CPOL=0, CPHA=0 (Low idle level, sample on leading edge)
# - Mode 1: CPOL=0, CPHA=1 (Low idle level, sample on trailing edge)
# - Mode 2: CPOL=1, CPHA=0 (High idle level, sample on falling edge)
# - Mode 3: CPOL=1, CPHA=1 (High idle level, sample on rising edge)
print("\nConfiguring SPI decoder...")
settings_spi["acq_speed"  ] = acq_rate      # Acquisition speed (must match decimation)
settings_spi["bit_order"  ] = "MsbFirst"    # Bit order: MsbFirst/LsbFirst
settings_spi["cpha"       ] = 0             # Clock phase: 0, 1
settings_spi["cpol"       ] = 0             # Clock polarity: 0, 1
settings_spi["cs_polarity"] = "ActiveLow"   # CS polarity: ActiveLow/ActiveHigh
settings_spi["invert_bit" ] = "No"          # Bit inversion: No/Yes
settings_spi["word_size"  ] = 8             # Word size: 7, 8 bits
settings_spi["clk"        ] = "DIN2"        # SPI CLK  pin: "DIN0" - "DIN7", "None" = disabled.
settings_spi["cs"         ] = "DIN3"        # SPI CS   pin: "DIN0" - "DIN7", "None" = disabled.
settings_spi["miso"       ] = "DIN0"        # SPI MISO pin: "DIN0" - "DIN7", "None" = disabled.
settings_spi["mosi"       ] = "DIN1"        # SPI MOSI pin: "DIN0" - "DIN7", "None" = disabled.
print(f"  SPI Mode:      Mode {settings_spi['cpol'] * 2 + settings_spi['cpha']} (CPOL={settings_spi['cpol']}, CPHA={settings_spi['cpha']})")
print(f"  Word size:     {settings_spi['word_size']} bits")
print(f"  SCLK pin:      {settings_spi['clk']}")


# I2C Decoder Settings
# --------------------
print("\nConfiguring I2C decoder...")
settings_i2c["acq_speed"     ] = 400000     # Acquisition speed (fixed to 400 kHz)
settings_i2c["address_format"] = "Shifted"  # Address format: Shifted/Unshifted
settings_i2c["invert_bit"    ] = "No"       # Bit inversion: No/Yes
settings_i2c["scl"           ] = "DIN0"          # I2C SCL pin: "DIN0" - "DIN7", "None" = disabled.
settings_i2c["sda"           ] = "DIN1"          # I2C SDA pin: "DIN0" - "DIN7", "None" = disabled.
print(f"  Speed:         {settings_i2c['acq_speed']} Hz ({settings_i2c['acq_speed']/1000:.0f} kHz)")
print(f"  Addr format:   {settings_i2c['address_format']}")
print(f"  SCL pin:       {settings_i2c['scl']}")
print(f"  SDA pin:       {settings_i2c['sda']}")


# CAN Decoder Settings
# --------------------
print("\nConfiguring CAN decoder...")
settings_can["acq_speed"       ] = acq_rate # Acquisition speed (must match decimation)
settings_can["fast_bitrate"    ] = 2000000  # Fast bitrate for CAN FD (2 Mbps)
settings_can["nominal_bitrate" ] = 200000   # Nominal bitrate for CAN 2.0 (200 kbps)
settings_can["invert_bit"      ] = "No"     # Bit inversion: No = normal, Yes = inverted
settings_can["rx"              ] = "DIN0"   # CAN RX pin: "DIN0" - "DIN7", "None" = disabled.
settings_can["sample_point"    ] = 87.5     # Sample point percentage. Integer between 0 and 100 (e.g., 80 for 80%) - (typically 75-87.5%)
print(f"  Nominal rate:  {settings_can['nominal_bitrate']} bps ({settings_can['nominal_bitrate']/1000:.0f} kbps)")
print(f"  Fast rate:     {settings_can['fast_bitrate']} bps ({settings_can['fast_bitrate']/1e6:.1f} Mbps)")
print(f"  Sample point:  {settings_can['sample_point']}%")
print(f"  RX pin:        {settings_can['rx']}")


# ==============================================================================
# SAVE SETTINGS - Export to JSON Files
# ==============================================================================

print("\n" + "=" * 70)
print("Saving Settings to JSON Files...")
print("=" * 70)

# Save UART settings
with open("settings_uart.json", "w", encoding='utf8') as json_file:
    json.dump(settings_uart, json_file, indent=4)
print("Saved: settings_uart.json")

# Save SPI settings
with open("settings_spi.json", "w", encoding='utf8') as json_file:
    json.dump(settings_spi, json_file, indent=4)
print("Saved: settings_spi.json")

# Save I2C settings
with open("settings_i2c.json", "w", encoding='utf8') as json_file:
    json.dump(settings_i2c, json_file, indent=4)
print("Saved: settings_i2c.json")

# Save CAN settings
with open("settings_can.json", "w", encoding='utf8') as json_file:
    json.dump(settings_can, json_file, indent=4)
print("Saved: settings_can.json")


# ==============================================================================
# CLEANUP - Release Resources
# ==============================================================================

print("\n" + "=" * 70)
print("Cleaning up resources...")

# Delete controller and free resources
del rp_cla
print("Logic Analyzer resources released")

print("\nProgram completed successfully")
print("All decoder settings have been saved to JSON files")
print("=" * 70)
