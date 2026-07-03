#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - I2C FPGA Loopback Example
======================================================

This example demonstrates real-time I2C protocol decoding using the Red Pitaya
Logic Analyzer in FPGA loopback mode. The script simultaneously generates I2C
traffic (reading from internal EEPROM) and captures/decodes it with the Logic
Analyzer. This is useful for verifying I2C communication, testing decoder
settings, and learning I2C protocol analysis.

Features:
- Real-time I2C bus capture and decode from FPGA
- Loopback connection between I2C peripheral and Logic Analyzer
- EEPROM read operation as I2C traffic source
- Configurable trigger and acquisition parameters
- RLE (Run Length Encoding) compression for efficient storage
- Automatic protocol decoding with annotations
- Data export to binary file for offline analysis

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Jumper wires for loopback connections

Required Connections:
=====================
Connect the I2C signals from Extension connector E2 to DIO pins on E1:
  - I2C SDA (E2) <-> any DIO_P pin (E1) (configured as DIO7_P in this example)
  - I2C SCL (E2) <-> any DIO_P pin (E1) (configured as DIO8_P in this example)

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Logic Analyzer module (rp_la)
- Red Pitaya Hardware module (rp_hw)
- NumPy library
- OS 2.00 or higher with Logic Analyzer FPGA image

Usage:
    python fpga_decode_2_i2c_loop.py
    
    The program will:
    1. Load the Logic Analyzer FPGA image
    2. Configure I2C to read from internal EEPROM
    3. Set up Logic Analyzer with I2C decoder
    4. Start acquisition and trigger on I2C activity
    5. Execute I2C EEPROM read
    6. Decode and display captured I2C transactions
    7. Save captured data to file

Configuration:
    Modify parameters in the CONFIGURATION sections:
    - I2C device address and EEPROM settings
    - I2C decoder pin assignments (SDA/SCL)
    - Logic Analyzer trigger and timing parameters
    - Decimation and sample rates

I2C Address Format:
    Shifted   = 0  (7-bit address shifted left by 1 bit)
    Unshifted = 1  (7-bit address in lower 7 bits)

Author: Red Pitaya
Date: January 2026
"""

import sys
import time
import rp_la
import rp_hw
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
# CONFIGURATION - I2C API Settings
# ==============================================================================

print("=" * 70)
print("Red Pitaya Logic Analyzer - I2C FPGA Loopback Example")
print("=" * 70)

# Hardware connection reminder
print("\n!! REQUIRED HARDWARE CONNECTIONS !!")
print("Before running, connect:")
print("  - I2C SDA (E2) <-> DIO1_P (E1)")
print("  - I2C SCL (E2) <-> DIO0_P (E1)")
print("=" * 70)

# I2C device configuration
dev_addr = 0b1010000                    # I2C device address (EEPROM)
eeprom_size = 8192                      # EEPROM size in bytes
page_size = 32                          # EEPROM page size
offset = 0x0000                         # Read offset address

print("\nI2C Configuration:")
print(f"  Device address:  0x{dev_addr:02X}")
print(f"  EEPROM size:     {eeprom_size} bytes")
print(f"  Page size:       {page_size} bytes")
print(f"  Read offset:     0x{offset:04X}")


# ==============================================================================
# CONFIGURATION - I2C Decoder Settings
# ==============================================================================

i2c_acq_speed = 4000000                 # Acquisition speed (4 MHz)
i2c_addr_format = "Shifted"             # Address format: "Shifted" or "Unshifted"
i2c_invert_bit = "No"                  # Bit inversion: "No" = normal, "Yes" = inverted
i2c_sda = "DIN1"                       # I2C SDA pin: "DIN0" - "DIN7", "None" = disabled
i2c_scl = "DIN0"                       # I2C SCL pin: "DIN0" - "DIN7", "None" = disabled

print("\nI2C Decoder Configuration:")
print(f"  Acquisition speed: {i2c_acq_speed} Hz")
print(f"  Address format:    {i2c_addr_format}")
print(f"  SDA pin:           {i2c_sda}")
print(f"  SCL pin:           {i2c_scl}")


# ==============================================================================
# CONFIGURATION - Logic Analyzer Acquisition
# ==============================================================================

trigger_ch = rp_la.LA_T_CHANNEL_1       # Trigger on channel 1 (SCL)
trig_edge = rp_la.LA_RISING_OR_FALLING  # Trigger on any edge

enable_RLE = True                       # Enable RLE compression
decimation = 32                         # Decimation factor
acq_rate = int(rp_hw_profiles.rp_HPGetBaseSpeedHzOrDefault() / decimation)
pre_trig_samples = int(125e6/decimation * 1e-3)   # 1 ms pre-trigger
post_trig_samples = int(125e6/decimation * 10e-3)  # 10 ms post-trigger

print("\nLogic Analyzer Acquisition:")
print(f"  Trigger channel:   Channel {trigger_ch}")
print("  Trigger edge:      Rising or Falling")
print(f"  Decimation:        {decimation}")
print(f"  Acquisition rate:  {acq_rate} Hz")
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
# I2C INITIALIZATION - Initialize I2C and configure settings
# ==============================================================================

print("\nInitializing I2C interface...")

# Initialize I2C device
res = rp_hw.rp_I2C_InitDevice("/dev/i2c-0", dev_addr)
if res:
    print(f"[ERROR] I2C initialization failed with code: {res}")
    sys.exit(1)
print("I2C device initialized successfully")

# Enable force mode for I2C
rp_hw.rp_I2C_setForceMode(True)
print("I2C force mode enabled")

# Prepare EEPROM address buffer
buff_addr = np.array([offset >> 8, offset & 0xFF], dtype=np.uint8)  # High byte, Low byte

# Create buffer for I2C read data
buff_i2c = np.zeros(page_size, dtype=np.uint8)
print(f"Buffers created: address buffer (2 bytes), data buffer ({page_size} bytes)")


# ==============================================================================
# LOGIC ANALYZER SETUP - Configure acquisition parameters
# ==============================================================================

print("\nConfiguring Logic Analyzer parameters...")

# Set acquisition parameters
rp_cla.setEnableRLE(enable_RLE)
rp_cla.setDecimation(decimation)
rp_cla.setTrigger(trigger_ch, trig_edge)
rp_cla.setPreTriggerSamples(pre_trig_samples)
rp_cla.setPostTriggerSamples(post_trig_samples)
print("Acquisition parameters configured")


# ==============================================================================
# DECODER SETUP - Add and configure I2C decoder
# ==============================================================================

print("\nConfiguring I2C decoder...")

# Add I2C decoder
rp_cla.addDecoder("I2C", rp_la.LA_DECODER_I2C)

# Configure decoder settings
rp_cla.setDecoderSettingsUInt("I2C", "acq_speed", acq_rate)
rp_cla.setDecoderSettingsString("I2C", "invert_bit", i2c_invert_bit)
rp_cla.setDecoderSettingsString("I2C", "address_format", i2c_addr_format)
rp_cla.setDecoderSettingsString("I2C", "scl", i2c_scl)
rp_cla.setDecoderSettingsString("I2C", "sda", i2c_sda)

# Display decoder settings
print("I2C decoder configured:")
print(f"  {rp_cla.getDecoderSettings('I2C')}")


# ==============================================================================
# ACQUISITION START - Begin capturing data
# ==============================================================================

print("\n" + "=" * 70)
print("Starting Data Acquisition and I2C Transaction")
print("=" * 70)

# Start asynchronous acquisition
rp_cla.runAsync(0)
print("Logic Analyzer acquisition started (waiting for trigger)")

# Wait for LA to be ready
time.sleep(0.1)

# Execute I2C transaction: Set EEPROM read address
print(f"Setting EEPROM read address to 0x{offset:04X}...")
rp_hw.rp_I2C_IOCTL_WriteBuffer(buff_addr)
time.sleep(6e-3)  # Wait 6 ms for write to complete

# Read data from EEPROM
print(f"Reading {page_size} bytes from EEPROM...")
rp_hw.rp_I2C_IOCTL_ReadBuffer(buff_i2c)

# Wait for trigger and acquisition to complete
print("Waiting for trigger and acquisition completion...")
res = rp_cla.wait(1000)  # Timeout: 1000 ms
if res:
    print("[ERROR] Acquisition timed out")
    sys.exit(1)
print("Acquisition completed successfully!")


# ==============================================================================
# DATA EXPORT - Save captured data to file
# ==============================================================================

print("\n" + "=" * 70)
print("Saving Captured Data")
print("=" * 70)

# Save raw captured data to file
output_file = "dump_i2c.bin"
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
# PROTOCOL DECODE - Decode and display I2C transactions
# ==============================================================================

print("\n" + "=" * 70)
print("DECODED I2C TRANSACTIONS")
print("=" * 70)

# Decode I2C protocol
decode = rp_cla.getDecodedData("I2C")
print(f"Found {len(decode)} decoded I2C events\n")

# Display each decoded event with annotation
if len(decode) > 0:
    print("Transaction Details:")
    print("-" * 70)
    for index in range(len(decode)):
        annotation = rp_cla.getAnnotation(rp_la.LA_DECODER_I2C, decode[index]['control'])
        print(f"Event {index + 1}: {annotation} = {decode[index]}")
    print("-" * 70)
else:
    print("No I2C transactions decoded")


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
