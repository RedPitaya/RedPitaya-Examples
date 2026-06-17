#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - Decoder Settings Export
====================================================

This example demonstrates how to retrieve default decoder settings from the
Red Pitaya Logic Analyzer and export them to JSON configuration files. The
script queries the Logic Analyzer for current decoder configurations and saves
them as templates that can be used for future protocol analysis or shared
between projects.

Features:
- Retrieve default decoder settings for all protocols
- Export settings to JSON configuration files
- Support for UART, SPI, I2C, and CAN decoders
- Create backup copies of decoder configurations
- Generate reusable configuration templates
- No modification of settings (save as-is)

Use Cases:
- Backup current decoder configurations
- Create baseline configuration templates
- Document default decoder settings
- Share decoder configurations between projects
- Export settings for offline review
- Generate starting points for custom configurations

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- No physical connections required (settings only)

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Logic Analyzer module (rp_la)
- Logic Analyzer FPGA image must be loaded
- OS 2.00 or higher

Usage:
    python la_settings_save_file.py
    
    The program will:
    1. Initialize Logic Analyzer controller
    2. Add decoders for UART, SPI, I2C, and CAN
    3. Retrieve current settings for each decoder
    4. Display settings to console
    5. Save settings to JSON files:
       - settings_uart.json
       - settings_spi.json
       - settings_i2c.json
       - settings_can.json

Output Files:
    The script generates JSON files containing the current decoder settings.
    These files can be:
    - Used as templates for custom configurations
    - Loaded by decoder applications
    - Modified and reused in other scripts
    - Shared with other users as configuration presets

Note:
    This script saves the default settings without modification. To customize
    settings, use la_settings_modify_file.py instead.

Author: Red Pitaya
Date: January 2026
"""

import json
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
# CONFIGURATION - Decoder Names
# ==============================================================================

print("=" * 70)
print("Red Pitaya Logic Analyzer - Decoder Settings Export")
print("=" * 70)

# Decoder identifiers
can_decoder = "CAN"
uart_decoder = "UART"
spi_decoder = "SPI"
i2c_decoder = "I2C"

print("\nDecoders to export:")
print(f"  - {uart_decoder}")
print(f"  - {spi_decoder}")
print(f"  - {i2c_decoder}")
print(f"  - {can_decoder}")


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
# RETRIEVE SETTINGS - Get Current Decoder Settings
# ==============================================================================

print("\n" + "=" * 70)
print("Retrieving Current Decoder Settings...")
print("=" * 70)

# Get settings from Red Pitaya
settings_uart = rp_cla.getDecoderSettings(uart_decoder)
settings_spi = rp_cla.getDecoderSettings(spi_decoder)
settings_i2c = rp_cla.getDecoderSettings(i2c_decoder)
settings_can = rp_cla.getDecoderSettings(can_decoder)

print(f"\nUART decoder settings:\n{settings_uart}")
print(f"\nSPI decoder settings:\n{settings_spi}")
print(f"\nI2C decoder settings:\n{settings_i2c}")
print(f"\nCAN decoder settings:\n{settings_can}")


# ==============================================================================
# PARSE SETTINGS - Convert JSON Strings to Dictionaries
# ==============================================================================

print("\n" + "=" * 70)
print("Parsing Settings...")
print("=" * 70)

# Parse JSON strings to dictionaries
settings_uart = json.loads(settings_uart)
settings_spi = json.loads(settings_spi)
settings_i2c = json.loads(settings_i2c)
settings_can = json.loads(settings_can)

print("Settings parsed successfully")
print(f"  UART: {len(settings_uart)} parameters")
print(f"  SPI:  {len(settings_spi)} parameters")
print(f"  I2C:  {len(settings_i2c)} parameters")
print(f"  CAN:  {len(settings_can)} parameters")


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
print("All decoder settings have been exported to JSON files")
print("=" * 70)
