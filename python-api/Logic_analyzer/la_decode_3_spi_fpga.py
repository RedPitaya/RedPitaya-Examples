#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - SPI External Signal Decoder
========================================================

This example demonstrates real-time SPI protocol decoding using the Red Pitaya
Logic Analyzer capturing external SPI bus signals. The script configures the
Logic Analyzer to trigger on SPI activity, capture bus data, and automatically
decode SPI transactions including MOSI, MISO data, chip select control, and
clock signals.

Features:
- Real-time SPI bus capture from external signals
- Support for all four SPI modes (CPOL/CPHA combinations)
- Configurable bit order (MSB-first or LSB-first)
- Word size configuration (7 or 8 bits)
- Chip Select polarity configuration (active-low/active-high)
- MISO and MOSI data decoding
- RLE (Run Length Encoding) compression for efficient storage
- Detailed protocol annotations for each decoded element
- Data export to binary file for offline analysis

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- External SPI device or bus with active traffic

Required Connections:
=====================
Connect external SPI signals to Red Pitaya DIO pins on Extension connector E1:
  - SPI MISO signal <-> DIO1_P (E1) (or any other DIO_P pin, configurable)
  - SPI MOSI signal <-> DIO2_P (E1) (or any other DIO_P pin, configurable)
  - SPI SCLK signal <-> DIO3_P (E1) (or any other DIO_P pin, configurable)
  - SPI CS signal   <-> DIO4_P (E1) (or any other DIO_P pin, configurable)

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Logic Analyzer module (rp_la)
- NumPy library
- OS 2.00 or higher with Logic Analyzer FPGA image

Usage:
    python la_decode_3_spi_fpga.py
    
    The program will:
    1. Load the Logic Analyzer FPGA image
    2. Configure SPI decoder with mode and timing
    3. Set up Logic Analyzer trigger and acquisition
    4. Wait for SPI bus activity to trigger capture
    5. Decode captured SPI transactions
    6. Display decoded protocol elements
    7. Save captured data to file

Configuration:
    Modify parameters in the CONFIGURATION sections:
    - SPI mode (CPOL/CPHA settings)
    - Bit order (MSB-first/LSB-first)
    - Word size (7 or 8 bits)
    - CS polarity (active-low/active-high)
    - MISO, MOSI, SCLK, and CS pin assignments
    - Logic Analyzer trigger and timing parameters
    - Decimation and sample rates

SPI Mode Settings:
    Mode 0 (CPOL=0, CPHA=0): Clock idle low, sample on leading edge
    Mode 1 (CPOL=0, CPHA=1): Clock idle low, sample on trailing edge
    Mode 2 (CPOL=1, CPHA=0): Clock idle high, sample on falling edge
    Mode 3 (CPOL=1, CPHA=1): Clock idle high, sample on rising edge

Author: Red Pitaya
Date: January 2026
"""

import sys
import time
import rp_la
import rp_hw_profiles
import numpy as np
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
# CONFIGURATION - SPI Decoder Settings
# ==============================================================================

print("=" * 70)
print("Red Pitaya Logic Analyzer - SPI External Signal Decoder")
print("=" * 70)

# Hardware connection reminder
print("\n!! REQUIRED HARDWARE CONNECTIONS !!")
print("Before running, connect:")
print("  - External SPI MISO signal <-> (Optional - set to None if not used)")
print("  - External SPI MOSI signal <-> DIO1_P (E1)")
print("  - External SPI SCLK signal <-> DIO0_P (E1)")
print("  - External SPI CS signal   <-> DIO2_P (E1)")
print("=" * 70)

# SPI decoder configuration
# Mode definitions:
# - CPOL=0, CPHA=0 (Mode 0): Low idle level, sample on leading edge
# - CPOL=0, CPHA=1 (Mode 1): Low idle level, sample on trailing edge
# - CPOL=1, CPHA=0 (Mode 2): High idle level, sample on leading edge
# - CPOL=1, CPHA=1 (Mode 3): High idle level, sample on trailing edge

dec_bit_order = "MsbFirst"              # Bit order: "MsbFirst" or "LsbFirst"
dec_cpha = 0                            # Clock phase (0 or 1)
dec_cpol = 0                            # Clock polarity (0 or 1)
dec_invert_bit = "No"                   # Bit inversion: "No" = normal, "Yes" = inverted
dec_word_size = 8                       # Word size (7 or 8 bits)
dec_cs_polarity = "ActiveLow"           # CS polarity: "ActiveLow" or "ActiveHigh"

# Pin assignments for SPI signals
dec_cs = "DIN2"                         # SPI CS pin: "DIN0" - "DIN7", "None" = disabled
dec_clk = "DIN0"                        # SPI CLK pin: "DIN0" - "DIN7", "None" = disabled
dec_miso = "None"                       # SPI MISO pin: "DIN0" - "DIN7", "None" = disabled
dec_mosi = "DIN1"                       # SPI MOSI pin: "DIN0" - "DIN7", "None" = disabled

print("\nSPI Decoder Configuration:")
print(f"  SPI Mode:          Mode {dec_cpol * 2 + dec_cpha} (CPOL={dec_cpol}, CPHA={dec_cpha})")
print(f"  Bit order:         {dec_bit_order}")
print(f"  Invert bit:        {dec_invert_bit}")
print(f"  Word size:         {dec_word_size} bits")
print(f"  CS polarity:       {dec_cs_polarity}")
print(f"  CS pin:            {dec_cs}")
print(f"  CLK pin:           {dec_clk}")
print(f"  MISO pin:          {dec_miso}")
print(f"  MOSI pin:          {dec_mosi}")


# ==============================================================================
# CONFIGURATION - Logic Analyzer Acquisition
# ==============================================================================

trigger_ch = rp_la.LA_T_CHANNEL_3       # Trigger on channel 3 (SCLK)
trig_edge = rp_la.LA_RISING_OR_FALLING  # Trigger on any edge

enable_RLE = True                       # Enable RLE compression
decimation = 8                          # Decimation factor
acq_rate = int(rp_hw_profiles.rp_HPGetBaseSpeedHzOrDefault() / decimation)
pre_trig_samples = int(125e6/decimation * 1e-3)   # 1 ms pre-trigger
post_trig_samples = int(125e6/decimation * 2e-3)  # 2 ms post-trigger

print("\nLogic Analyzer Acquisition:")
print(f"  Trigger channel:   Channel {trigger_ch}")
print(f"  Trigger edge:      Rising or Falling")
print(f"  Decimation:        {decimation}")
print(f"  Acquisition rate:  {acq_rate} Hz ({acq_rate/1e6:.2f} MHz)")
print(f"  Pre-trigger:       {pre_trig_samples} samples")
print(f"  Post-trigger:      {post_trig_samples} samples")
print(f"  RLE compression:   {'Enabled' if enable_RLE else 'Disabled'}")


# ==============================================================================
# FPGA INITIALIZATION - Load Logic Analyzer FPGA image
# ==============================================================================

print("\n" + "=" * 70)
print("Initializing FPGA and Logic Analyzer...")
print("=" * 70)

# Change FPGA image to Logic Analyzer
fpga = overlay("logic")
print("Logic Analyzer FPGA image loaded")

# Create Logic Analyzer controller and initialize
rp_cla = rp_la.CLAController()
rp_cla.initFpga()
print("Logic Analyzer controller initialized")

# Set callback for events
callback = Callback()
rp_cla.setDelegate(callback.__disown__())
print("Event callback registered")


# ==============================================================================
# LOGIC ANALYZER SETUP - Configure acquisition parameters
# ==============================================================================

print("\nConfiguring Logic Analyzer parameters...")

# Set acquisition parameters
rp_cla.setEnableRLE(True)
rp_cla.setDecimation(decimation)
rp_cla.setTrigger(trigger_ch, trig_edge)
rp_cla.setPreTriggerSamples(pre_trig_samples)
rp_cla.setPostTriggerSamples(post_trig_samples)
print("Acquisition parameters configured")


# ==============================================================================
# DECODER SETUP - Add and configure SPI decoder
# ==============================================================================

print("\nConfiguring SPI decoder...")

# Add SPI decoder
rp_cla.addDecoder("SPI", rp_la.LA_DECODER_SPI)

# Configure decoder settings
rp_cla.setDecoderSettingsUInt("SPI", "acq_speed", acq_rate)
rp_cla.setDecoderSettingsUInt("SPI", "bit_order", dec_bit_order)
rp_cla.setDecoderSettingsUInt("SPI", "cpha", dec_cpha)
rp_cla.setDecoderSettingsUInt("SPI", "cpol", dec_cpol)
rp_cla.setDecoderSettingsUInt("SPI", "invert_bit", dec_invert_bit)
rp_cla.setDecoderSettingsUInt("SPI", "word_size", dec_word_size)
rp_cla.setDecoderSettingsUInt("SPI", "cs_polarity", dec_cs_polarity)
rp_cla.setDecoderSettingsUInt("SPI", "cs", dec_cs)
rp_cla.setDecoderSettingsUInt("SPI", "clk", dec_clk)
rp_cla.setDecoderSettingsUInt("SPI", "miso", dec_miso)
rp_cla.setDecoderSettingsUInt("SPI", "mosi", dec_mosi)
print("SPI decoder configured")


# ==============================================================================
# ACQUISITION START - Begin capturing data
# ==============================================================================

print("\n" + "=" * 70)
print("Starting Data Acquisition")
print("=" * 70)

# Start asynchronous acquisition
rp_cla.runAsync(0)
print("Logic Analyzer acquisition started")
print("Waiting for SPI bus activity to trigger capture...")

# Wait for initial data acquisition
time.sleep(0.1)

# Wait for trigger (no timeout - wait indefinitely for SPI traffic)
print("\nWaiting for trigger...")
res = rp_cla.wait(0)  # Timeout: 0 = no timeout
if res:
    print("[ERROR] Acquisition timed out")
    sys.exit(1)
print("Trigger detected! Acquisition completed successfully!")


# ==============================================================================
# DATA EXPORT - Save captured data to file
# ==============================================================================

print("\n" + "=" * 70)
print("Saving Captured Data")
print("=" * 70)

# Save raw captured data to file
output_file = "spi_data.bin"
rp_cla.saveCaptureDataToFile(output_file)
print(f"Captured data saved to: {output_file}")


# ==============================================================================
# DATA ANALYSIS - Display captured and unpacked data
# ==============================================================================

print("\n" + "=" * 70)
print("Captured Data Analysis")
print("=" * 70)

# Get packed (RLE) data
rawBytesCount = rp_cla.getCapturedDataSize()
raw_data = np.zeros(rawBytesCount, dtype=np.uint8)
packed_count = rp_cla.getDataNP(raw_data)
print(f"Packed RLE samples: {packed_count} bytes")

# Get unpacked data
rle_data = np.zeros(rp_cla.getCapturedSamples(), dtype=np.uint8)
unpacked_count = rp_cla.getUnpackedRLEDataNP(rle_data)
print(f"Unpacked samples:   {unpacked_count}")

print(f"\nRLE (packed) data:    {raw_data}")
print(f"Unpacked data:        {rle_data}")

# Print RLE information
print("\nRLE Compression Details:")
rp_cla.printRLE(False)


# ==============================================================================
# PROTOCOL DECODE - Decode and display SPI transactions
# ==============================================================================

print("\n" + "=" * 70)
print("DECODED SPI TRANSACTIONS")
print("=" * 70)

# Decode SPI protocol
decode = rp_cla.getDecodedData("SPI")
print(f"Found {len(decode)} decoded SPI events\n")

# Display each decoded event with annotation
if len(decode) > 0:
    print("Transaction Details:")
    print("-" * 70)
    for index in range(len(decode)):
        annotation = rp_cla.getAnnotation(rp_la.LA_DECODER_SPI, decode[index]['control'])
        print(f"Event {index + 1}: {annotation} = {decode[index]}")
    print("-" * 70)
else:
    print("No SPI transactions decoded")


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\n" + "=" * 70)
print("Cleaning up resources...")

# Delete controller and free resources
del rp_cla
print("Logic Analyzer resources released")

print("\nProgram completed successfully")
print("=" * 70)
