#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - UART Decoder from File
===================================================

This example demonstrates how to decode UART (Universal Asynchronous
Receiver/Transmitter) serial data that was previously captured and saved to
a file using the Red Pitaya Logic Analyzer. The decoder reads captured binary
data and a JSON configuration file, then decodes and displays UART frames
including data bytes, parity information, and framing errors.

Features:
- Load captured UART data from binary file
- Load decoder settings from JSON configuration file
- Decode UART frames with start/stop bits, data, and parity
- Display decoded characters and bytes with annotations
- Support for various baud rates and data formats
- Configurable parity, stop bits, and bit order

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Previously captured UART data (dump_uart.bin)
- UART decoder settings file (settings_uart.json)

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Logic Analyzer module (rp_la)
- OS 2.00 or higher

Usage:
    python file_decode_4_uart.py
    
    The program will load the captured UART data from dump_uart.bin,
    apply the decoder settings from settings_uart.json, and display
    all decoded UART frames.

Required Files:
    - dump_uart.bin: Binary file containing captured UART data
    - settings_uart.json: JSON file with UART decoder configuration
      (baud rate, data bits, parity, stop bits, pin assignments)

UART Configuration Constants:

Bit Order:
    LSB_FIRST = 0  (Least significant bit first)
    MSB_FIRST = 1  (Most significant bit first)

Number of Data Bits:
    DATA_BITS_5 = 5
    DATA_BITS_6 = 6
    DATA_BITS_7 = 7
    DATA_BITS_8 = 8
    DATA_BITS_9 = 9

Parity:
    NONE     = 0  (No parity)
    EVEN     = 1  (Even parity)
    ODD      = 2  (Odd parity)
    ALWAYS_0 = 3  (Parity bit always 0)
    ALWAYS_1 = 4  (Parity bit always 1)

Number of Stop Bits:
    STOP_BITS_NO = 0  (No stop bits)
    STOP_BITS_05 = 1  (0.5 stop bits)
    STOP_BITS_10 = 2  (1.0 stop bit)
    STOP_BITS_15 = 3  (1.5 stop bits)
    STOP_BITS_20 = 4  (2.0 stop bits)

Author: Red Pitaya
Date: January 2026
"""

import rp_la


# ==============================================================================
# CONFIGURATION - File paths for captured data and settings
# ==============================================================================

# Input files
data_file = "dump_uart.bin"           # Binary file with captured UART data
settings_file = "settings_uart.json"  # JSON file with decoder settings

# Decoder name
decoder_name = "UART"

print("=" * 70)
print("Red Pitaya Logic Analyzer - UART Decoder from File")
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
# LOAD DATA - Load captured UART data from binary file
# ==============================================================================

print(f"\nLoading captured data from {data_file}...")

# Load data from file
# Parameters: filename, compressed (True for .bin files), channel offset
rp_cla.loadFromFile(data_file, True, 0)
print("Captured data loaded successfully")


# ==============================================================================
# DECODER SETUP - Add UART decoder and load settings
# ==============================================================================

print(f"\nSetting up {decoder_name} decoder...")

# Add UART decoder
rp_cla.addDecoder(decoder_name, rp_la.LA_DECODER_UART)
print(f"{decoder_name} decoder added")

# Load decoder settings from JSON file
print(f"Loading decoder settings from {settings_file}...")
with open(settings_file, "r", encoding='utf8') as f:
    settings_json = f.read()
    rp_cla.setDecoderSettings(decoder_name, settings_json)
print("Decoder settings loaded and applied")


# ==============================================================================
# DISPLAY SETTINGS - Show current decoder configuration
# ==============================================================================

print("\n" + "=" * 70)
print("UART DECODER SETTINGS")
print("=" * 70)

# Get and display current settings
current_settings = rp_cla.getDecoderSettings(decoder_name)
print(current_settings)

print("\nUART Configuration Options:")
print("\nBit Order:")
print("  LSB_FIRST = 0  (Least significant bit first)")
print("  MSB_FIRST = 1  (Most significant bit first)")
print("\nData Bits:")
print("  DATA_BITS_5 = 5")
print("  DATA_BITS_6 = 6")
print("  DATA_BITS_7 = 7")
print("  DATA_BITS_8 = 8")
print("  DATA_BITS_9 = 9")
print("\nParity:")
print("  NONE     = 0  (No parity)")
print("  EVEN     = 1  (Even parity)")
print("  ODD      = 2  (Odd parity)")
print("  ALWAYS_0 = 3  (Parity bit always 0)")
print("  ALWAYS_1 = 4  (Parity bit always 1)")
print("\nStop Bits:")
print("  STOP_BITS_NO = 0  (No stop bits)")
print("  STOP_BITS_05 = 1  (0.5 stop bits)")
print("  STOP_BITS_10 = 2  (1.0 stop bit)")
print("  STOP_BITS_15 = 3  (1.5 stop bits)")
print("  STOP_BITS_20 = 4  (2.0 stop bits)")


# ==============================================================================
# DECODE DATA - Process captured data and display results
# ==============================================================================

print("\n" + "=" * 70)
print("DECODED UART FRAMES")
print("=" * 70)

# Decode the captured data
print("\nDecoding UART serial data...")
decode = rp_cla.decode(decoder_name)
print(f"Found {len(decode)} decoded UART frames\n")

# Display decoded frames with annotations
if len(decode) > 0:
    print("Frame Details:")
    print("-" * 70)
    for index in range(len(decode)):
        annotation = rp_cla.getAnnotation(rp_la.LA_DECODER_UART, decode[index]['control'])
        print(f"Frame {index + 1}: {annotation} = {decode[index]}")
    print("-" * 70)
else:
    print("No UART frames found in the captured data")


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
