#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - I2C External Signal Decoder
========================================================

This example demonstrates real-time I2C protocol decoding using the Red Pitaya
Logic Analyzer capturing external I2C bus signals. The script configures the
Logic Analyzer to trigger on I2C activity, capture bus data, and automatically
decode I2C transactions including start/stop conditions, addresses, data bytes,
and ACK/NACK responses.

Features:
- Real-time I2C bus capture from external signals
- Support for 7-bit and 10-bit addressing
- Configurable address format (shifted/unshifted)
- Automatic detection of start, stop, repeated start conditions
- ACK/NACK bit decoding
- Read/Write operation identification
- RLE (Run Length Encoding) compression for efficient storage
- Detailed protocol annotations for each decoded element
- Data export to binary file for offline analysis

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- External I2C device or bus with active traffic
- Pull-up resistors on SDA and SCL lines (typically 4.7kΩ to 10kΩ)

Required Connections:
=====================
Connect external I2C signals to Red Pitaya DIO pins on Extension connector E1:
  - I2C SDA signal <-> DIO7_P (E1) (or any other DIO_P pin, configurable)
  - I2C SCL signal <-> DIO8_P (E1) (or any other DIO_P pin, configurable)

Note: Ensure proper pull-up resistors are present on both SDA and SCL lines.
The I2C bus operates with open-drain outputs requiring pull-ups.

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Logic Analyzer module (rp_la)
- NumPy library
- OS 2.00 or higher with Logic Analyzer FPGA image

Usage:
    python la_decode_2_i2c_fpga.py
    
    The program will:
    1. Load the Logic Analyzer FPGA image
    2. Configure I2C decoder with address format
    3. Set up Logic Analyzer trigger and acquisition
    4. Wait for I2C bus activity to trigger capture
    5. Decode captured I2C transactions
    6. Display decoded protocol elements
    7. Save captured data to file

Configuration:
    Modify parameters in the CONFIGURATION sections:
    - I2C address format (shifted/unshifted)
    - SDA and SCL pin assignments
    - Logic Analyzer trigger and timing parameters
    - Decimation and sample rates

I2C Address Format:
    Shifted   = 0: 7-bit address shifted left by 1 bit (R/W in LSB)
    Unshifted = 1: 7-bit address in lower 7 bits

Common I2C speeds: 100 kHz (Standard), 400 kHz (Fast), 1 MHz (Fast Plus)

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
# CONFIGURATION - I2C Decoder Settings
# ==============================================================================

print("=" * 70)
print("Red Pitaya Logic Analyzer - I2C External Signal Decoder")
print("=" * 70)

# Hardware connection reminder
print("\n!! REQUIRED HARDWARE CONNECTIONS !!")
print("Before running, connect:")
print("  - External I2C SDA signal <-> DIO1_P (E1)")
print("  - External I2C SCL signal <-> DIO0_P (E1)")
print("  (Ensure pull-up resistors are present on SDA and SCL)")
print("=" * 70)

# I2C decoder configuration
i2c_acq_speed = 4000000                 # Acquisition speed (4 MHz)
i2c_addr_format = "Shifted"             # Address format: "Shifted" or "Unshifted"
i2c_invert_bit = "No"                  # Bit inversion: "No" = normal, "Yes" = inverted
i2c_sda = "DIN1"                       # I2C SDA pin: "DIN0" - "DIN7", "None" = disabled
i2c_scl = "DIN0"                       # I2C SCL pin: "DIN0" - "DIN7", "None" = disabled

print("\nI2C Decoder Configuration:")
print(f"  Acquisition speed: {i2c_acq_speed} Hz ({i2c_acq_speed/1000:.0f} kHz)")
print(f"  Address format:    {i2c_addr_format}")
print(f"  Invert bit:        {i2c_invert_bit}")
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
post_trig_samples = int(125e6/decimation * 3e-3)  # 3 ms post-trigger

print("\nLogic Analyzer Acquisition:")
print(f"  Trigger channel:   Channel {trigger_ch}")
print("  Trigger edge:      Rising or Falling")
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
print("Starting Data Acquisition")
print("=" * 70)

# Start asynchronous acquisition
rp_cla.runAsync(0)
print("Logic Analyzer acquisition started")
print("Waiting for I2C bus activity to trigger capture...")

# Wait for initial data acquisition
time.sleep(0.1)

# Wait for trigger (no timeout - wait indefinitely for I2C traffic)
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
output_file = "i2c_data.bin"
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
