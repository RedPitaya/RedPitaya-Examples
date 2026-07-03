#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - SPI Decoder from File
==================================================

This example demonstrates how to decode SPI (Serial Peripheral Interface) bus
data that was previously captured and saved to a file using the Red Pitaya Logic
Analyzer. The decoder reads captured binary data and a JSON configuration file,
then decodes and displays SPI transactions including MOSI/MISO data exchanges,
clock polarity, and phase information.

Features:
- Load captured SPI bus data from binary file
- Load decoder settings from JSON configuration file
- Decode SPI transactions with MOSI and MISO data
- Display decoded data bytes with annotations
- Support for multiple SPI modes (CPOL/CPHA configurations)
- Configurable word size and bit order

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Previously captured SPI bus data (dump_spi.bin)
- SPI decoder settings file (settings_spi.json)

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Logic Analyzer module (rp_la)
- OS 2.00 or higher

Usage:
    python file_decode_3_spi.py
    
    The program will load the captured SPI data from dump_spi.bin,
    apply the decoder settings from settings_spi.json, and display
    all decoded SPI transactions.

Required Files:
    - dump_spi.bin: Binary file containing captured SPI bus data
    - settings_spi.json: JSON file with SPI decoder configuration
      (CLK/MOSI/MISO/CS pin assignments, CPOL/CPHA, bit order)

SPI Configuration Constants:

Chip Select Polarity:
    ActiveLow  = 0  (CS active when low)
    ActiveHigh = 1  (CS active when high)

Bit Order:
    MsbFirst = 0  (Most significant bit first)
    LsbFirst = 1  (Least significant bit first)

SPI Modes (CPOL/CPHA combinations):
    Mode 0: CPOL=0, CPHA=0 (Low idle, sample on leading edge)
    Mode 1: CPOL=0, CPHA=1 (Low idle, sample on trailing edge)
    Mode 2: CPOL=1, CPHA=0 (High idle, sample on leading edge)
    Mode 3: CPOL=1, CPHA=1 (High idle, sample on trailing edge)

Author: Red Pitaya
Date: January 2026
"""

import rp_la


# ==============================================================================
# CONFIGURATION - File paths for captured data and settings
# ==============================================================================

# Input files
data_file = "dump_spi.bin"           # Binary file with captured SPI data
settings_file = "settings_spi.json"  # JSON file with decoder settings

# Decoder name
decoder_name = "SPI"

print("=" * 70)
print("Red Pitaya Logic Analyzer - SPI Decoder from File")
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
# LOAD DATA - Load captured SPI data from binary file
# ==============================================================================

print(f"\nLoading captured data from {data_file}...")

# Load data from file
# Parameters: filename, compressed (True for .bin files), channel offset
rp_cla.loadFromFile(data_file, True, 0)
print("Captured data loaded successfully")


# ==============================================================================
# DECODER SETUP - Add SPI decoder and load settings
# ==============================================================================

print(f"\nSetting up {decoder_name} decoder...")

# Add SPI decoder
rp_cla.addDecoder(decoder_name, rp_la.LA_DECODER_SPI)
print(f"{decoder_name} decoder added")

# Load decoder settings from JSON file
print(f"Loading decoder settings from {settings_file}...")
with open(settings_file, "r", encoding='utf-8') as f:
    settings_json = f.read()
    rp_cla.setDecoderSettings(decoder_name, settings_json)
print("Decoder settings loaded and applied")


# ==============================================================================
# DISPLAY SETTINGS - Show current decoder configuration
# ==============================================================================

print("\n" + "=" * 70)
print("SPI DECODER SETTINGS")
print("=" * 70)

# Get and display current settings
current_settings = rp_cla.getDecoderSettings(decoder_name)
print(current_settings)

print("\nSPI Configuration Options:")
print("\nChip Select Polarity:")
print("  ActiveLow  = 0  (CS active when low)")
print("  ActiveHigh = 1  (CS active when high)")
print("\nBit Order:")
print("  MsbFirst = 0  (Most significant bit first)")
print("  LsbFirst = 1  (Least significant bit first)")
print("\nSPI Modes:")
print("  Mode 0: CPOL=0, CPHA=0 (Low idle, sample on leading)")
print("  Mode 1: CPOL=0, CPHA=1 (Low idle, sample on trailing)")
print("  Mode 2: CPOL=1, CPHA=0 (High idle, sample on leading)")
print("  Mode 3: CPOL=1, CPHA=1 (High idle, sample on trailing)")


# ==============================================================================
# DECODE DATA - Process captured data and display results
# ==============================================================================

print("\n" + "=" * 70)
print("DECODED SPI TRANSACTIONS")
print("=" * 70)

# Decode the captured data
print("\nDecoding SPI bus data...")
decode = rp_cla.decode(decoder_name)
print(f"Found {len(decode)} decoded SPI events\n")

# Display decoded transactions with annotations
if len(decode) > 0:
    print("Transaction Details:")
    print("-" * 70)
    for index in range(len(decode)):
        annotation = rp_cla.getAnnotation(rp_la.LA_DECODER_SPI, decode[index]['control'])
        print(f"Event {index + 1}: {annotation} = {decode[index]}")
    print("-" * 70)
else:
    print("No SPI transactions found in the captured data")


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
