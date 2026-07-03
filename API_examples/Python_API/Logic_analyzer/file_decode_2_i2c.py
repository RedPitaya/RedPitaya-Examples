#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - I2C Decoder from File
==================================================

This example demonstrates how to decode I2C (Inter-Integrated Circuit) bus data
that was previously captured and saved to a file using the Red Pitaya Logic
Analyzer. The decoder reads captured binary data and a JSON configuration file,
then decodes and displays I2C transactions including start/stop conditions,
addresses, data bytes, and ACK/NACK responses.

Features:
- Load captured I2C bus data from binary file
- Load decoder settings from JSON configuration file
- Decode I2C transactions with addresses and data
- Display decoded messages with annotations
- Support for 7-bit and 10-bit I2C addressing
- Address format options (shifted/unshifted)

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Previously captured I2C bus data (dump_i2c.bin)
- I2C decoder settings file (settings_i2c.json)

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Logic Analyzer module (rp_la)
- OS 2.00 or higher

Usage:
    python file_decode_2_i2c.py
    
    The program will load the captured I2C data from dump_i2c.bin,
    apply the decoder settings from settings_i2c.json, and display
    all decoded I2C transactions.

Required Files:
    - dump_i2c.bin: Binary file containing captured I2C bus data
    - settings_i2c.json: JSON file with I2C decoder configuration
      (SCL/SDA pin assignments, address format)

I2C Address Format Constants:
    Shifted   = 0  (7-bit address shifted left by 1 bit)
    Unshifted = 1  (7-bit address in lower 7 bits)

Author: Red Pitaya
Date: January 2026
"""

import rp_la


# ==============================================================================
# CONFIGURATION - File paths for captured data and settings
# ==============================================================================

# Input files
data_file = "dump_i2c.bin"           # Binary file with captured I2C data
settings_file = "settings_i2c.json"  # JSON file with decoder settings

# Decoder name
decoder_name = "I2C"

print("=" * 70)
print("Red Pitaya Logic Analyzer - I2C Decoder from File")
print("=" * 70)
print(f"Data file:     {data_file}")
print(f"Settings file: {settings_file}")
print(f"Decoder:       {decoder_name}")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Create Logic Analyzer controller
# ==============================================================================

print("\nInitializing Logic Analyzer controller...")

# Create controller instance
rp_cla = rp_la.CLAController()
print("Logic Analyzer controller created")


# ==============================================================================
# LOAD DATA - Load captured I2C data from binary file
# ==============================================================================

print(f"\nLoading captured data from {data_file}...")

# Load data from file
# Parameters: filename, compressed (True for .bin files), channel offset
rp_cla.loadFromFile(data_file, True, 0)
print("Captured data loaded successfully")


# ==============================================================================
# DECODER SETUP - Add I2C decoder and load settings
# ==============================================================================

print(f"\nSetting up {decoder_name} decoder...")

# Add I2C decoder
rp_cla.addDecoder(decoder_name, rp_la.LA_DECODER_I2C)
print(f"{decoder_name} decoder added")

# Load decoder settings from JSON file
print(f"Loading decoder settings from {settings_file}...")
with open(settings_file, "r", encoding="utf-8") as f:
    settings_json = f.read()
    rp_cla.setDecoderSettings(decoder_name, settings_json)
print("Decoder settings loaded and applied")


# ==============================================================================
# DISPLAY SETTINGS - Show current decoder configuration
# ==============================================================================

print("\n" + "=" * 70)
print("I2C DECODER SETTINGS")
print("=" * 70)

# Get and display current settings
current_settings = rp_cla.getDecoderSettings(decoder_name)
print(current_settings)

print("\nI2C Address Format Options:")
print("  Shifted   = 0  (7-bit address shifted left by 1 bit)")
print("  Unshifted = 1  (7-bit address in lower 7 bits)")


# ==============================================================================
# DECODE DATA - Process captured data and display results
# ==============================================================================

print("\n" + "=" * 70)
print("DECODED I2C TRANSACTIONS")
print("=" * 70)

# Decode the captured data
print("\nDecoding I2C bus data...")
decode = rp_cla.decode(decoder_name)
print(f"Found {len(decode)} decoded I2C events\n")

# Display decoded transactions with annotations
if len(decode) > 0:
    print("Transaction Details:")
    print("-" * 70)
    for index in range(len(decode)):
        annotation = rp_cla.getAnnotation(rp_la.LA_DECODER_I2C, decode[index]['control'])
        print(f"Event {index + 1}: {annotation} = {decode[index]}")
    print("-" * 70)
else:
    print("No I2C transactions found in the captured data")


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\n" + "=" * 70)
print("Cleaning up...")

# Delete controller and free resources
del rp_cla
print("Logic Analyzer controller released")

print("\nProgram completed successfully")
print("=" * 70)
