#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - CAN Bus Decoder from File
======================================================

This example demonstrates how to decode CAN (Controller Area Network) bus data
that was previously captured and saved to a file using the Red Pitaya Logic
Analyzer. The decoder reads captured binary data and a JSON configuration file,
then decodes and displays CAN frames including frame IDs, data, and control
information.

Features:
- Load captured CAN bus data from binary file
- Load decoder settings from JSON configuration file
- Decode CAN frames with frame ID, data bytes, and control information
- Display decoded CAN messages with annotations
- Support for standard and extended CAN frame formats

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Previously captured CAN bus data (dump_can.bin)
- CAN decoder settings file (settings_can.json)

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Logic Analyzer module (rp_la)
- OS 2.00 or higher

Usage:
    python file_decode_1_can.py
    
    The program will load the captured CAN data from dump_can.bin,
    apply the decoder settings from settings_can.json, and display
    all decoded CAN frames.

Required Files:
    - dump_can.bin: Binary file containing captured CAN bus data
    - settings_can.json: JSON file with CAN decoder configuration
      (bit rate, sample point, signal assignments)

Author: Red Pitaya
Date: January 2026
"""

import rp_la


# ==============================================================================
# CONFIGURATION - File paths for captured data and settings
# ==============================================================================

# Input files
data_file = "dump_can.bin"          # Binary file with captured CAN data
settings_file = "settings_can.json"  # JSON file with decoder settings

# Decoder name
decoder_name = "CAN"

print("=" * 70)
print("Red Pitaya Logic Analyzer - CAN Bus Decoder from File")
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
# LOAD DATA - Load captured CAN data from binary file
# ==============================================================================

print(f"\nLoading captured data from {data_file}...")

# Load data from file
# Parameters: filename, compressed (True for .bin files), channel offset
rp_cla.loadFromFile(data_file, True, 0)
print("Captured data loaded successfully")


# ==============================================================================
# DECODER SETUP - Add CAN decoder and load settings
# ==============================================================================

print(f"\nSetting up {decoder_name} decoder...")

# Add CAN decoder
rp_cla.addDecoder(decoder_name, rp_la.LA_DECODER_CAN)
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
print("CAN DECODER SETTINGS")
print("=" * 70)

# Get and display current settings
current_settings = rp_cla.getDecoderSettings(decoder_name)
print(current_settings)


# ==============================================================================
# DECODE DATA - Process captured data and display results
# ==============================================================================

print("\n" + "=" * 70)
print("DECODED CAN FRAMES")
print("=" * 70)

# Decode the captured data
print("\nDecoding CAN bus data...")
decode = rp_cla.decode(decoder_name)
print(f"Found {len(decode)} decoded CAN frames\n")

# Display decoded frames with annotations
if len(decode) > 0:
    print("Frame Details:")
    print("-" * 70)
    for index in range(len(decode)):
        annotation = rp_cla.getAnnotation(rp_la.LA_DECODER_CAN, decode[index]['control'])
        print(f"Frame {index + 1}: {annotation} = {decode[index]}")
    print("-" * 70)
else:
    print("No CAN frames found in the captured data")


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
