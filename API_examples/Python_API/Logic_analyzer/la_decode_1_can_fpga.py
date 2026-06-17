#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - CAN External Signal Decoder
========================================================

This example demonstrates real-time CAN protocol decoding using the Red Pitaya
Logic Analyzer capturing external CAN bus signals. The script configures the
Logic Analyzer to trigger on CAN activity, capture bus data, and automatically
decode CAN frames including arbitration, data, and control fields.

Features:
- Real-time CAN bus capture from external signals
- Support for CAN 2.0 and CAN FD protocols
- Configurable nominal and fast bitrates
- Automatic frame detection and decoding
- Sample point configuration for timing optimization
- RLE (Run Length Encoding) compression for efficient storage
- Detailed protocol annotations for each decoded element
- Data export to binary file for offline analysis

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- External CAN transceiver connected to DIO pins
- CAN bus with active traffic

Required Connections:
=====================
Connect external CAN signals to Red Pitaya DIO pins on Extension connector E1:
  - CAN RX signal <-> DIO1_P (E1) (or any other DIO_P pin, configurable)

Note: The CAN transceiver must convert the differential CAN bus signals
(CAN_H, CAN_L) to a single-ended signal suitable for the Logic Analyzer input.

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Logic Analyzer module (rp_la)
- NumPy library
- OS 2.00 or higher with Logic Analyzer FPGA image

Usage:
    python la_decode_1_can_fpga.py
    
    The program will:
    1. Load the Logic Analyzer FPGA image
    2. Configure CAN decoder with bitrate settings
    3. Set up Logic Analyzer trigger and acquisition
    4. Wait for CAN bus activity to trigger capture
    5. Decode captured CAN frames
    6. Display decoded protocol elements
    7. Save captured data to file

Configuration:
    Modify parameters in the CONFIGURATION sections:
    - CAN nominal and fast bitrates (for CAN FD)
    - Sample point percentage (timing optimization)
    - CAN RX pin assignment
    - Logic Analyzer trigger and timing parameters
    - Decimation and sample rates

CAN Protocol Settings:
    Nominal bitrate: Standard CAN 2.0 data rate (typically 125k-1M bps)
    Fast bitrate:    CAN FD data phase rate (up to 8M bps)
    Sample point:    Bit timing parameter (typically 75-87.5%)
    
    Common CAN bitrates: 125000, 250000, 500000, 1000000 bps

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
# CONFIGURATION - CAN Decoder Settings
# ==============================================================================

print("=" * 70)
print("Red Pitaya Logic Analyzer - CAN External Signal Decoder")
print("=" * 70)

# Hardware connection reminder
print("\n!! REQUIRED HARDWARE CONNECTIONS !!")
print("Before running, connect:")
print("  - External CAN RX signal <-> DIO1_P (E1)")
print("  (CAN transceiver required to convert differential CAN bus)")
print("=" * 70)

# CAN decoder configuration
can_decoder = "CAN"
dec_nominal_bitrate = 200000            # Nominal bitrate for CAN 2.0 (200 kbps)
dec_fast_bitrate = 2000000              # Fast bitrate for CAN FD (2 Mbps)
dec_sample_point = 87.5                 # Sample point percentage (87.5%) - must be integer between 0-100
dec_invert_bit = "No"                   # Bit inversion: "No" = normal, "Yes" = inverted
dec_rx = "DIN0"                         # CAN RX pin: "DIN0" - "DIN7", "None" = disabled

print("\nCAN Decoder Configuration:")
print(f"  Nominal bitrate:   {dec_nominal_bitrate} bps ({dec_nominal_bitrate/1000:.0f} kbps)")
print(f"  Fast bitrate:      {dec_fast_bitrate} bps ({dec_fast_bitrate/1e6:.1f} Mbps)")
print(f"  Sample point:      {dec_sample_point}%")
print(f"  Invert bit:        {dec_invert_bit}")
print(f"  RX pin:            {dec_rx}")


# ==============================================================================
# CONFIGURATION - Logic Analyzer Acquisition
# ==============================================================================

trigger_ch = rp_la.LA_T_CHANNEL_1       # Trigger on channel 1 (CAN RX)
trig_edge = rp_la.LA_RISING_OR_FALLING  # Trigger on any edge

enable_RLE = True                       # Enable RLE compression
decimation = 16                         # Decimation factor
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
# DECODER SETUP - Add and configure CAN decoder
# ==============================================================================

print("\nConfiguring CAN decoder...")

# Add CAN decoder
rp_cla.addDecoder(can_decoder, rp_la.LA_DECODER_CAN)

# Configure decoder settings
rp_cla.setDecoderSettingsUInt(can_decoder, "acq_speed", acq_rate)
rp_cla.setDecoderSettingsString(can_decoder, "invert_bit", dec_invert_bit)
rp_cla.setDecoderSettingsUInt(can_decoder, "fast_bitrate", dec_fast_bitrate)
rp_cla.setDecoderSettingsUInt(can_decoder, "nominal_bitrate", dec_nominal_bitrate)
rp_cla.setDecoderSettingsString(can_decoder, "rx", dec_rx)
rp_cla.setDecoderSettingsFloat(can_decoder, "sample_point", dec_sample_point)

# Display decoder settings
print("CAN decoder configured:")
print(f"  {rp_cla.getDecoderSettings(can_decoder)}")


# ==============================================================================
# ACQUISITION START - Begin capturing data
# ==============================================================================

print("\n" + "=" * 70)
print("Starting Data Acquisition")
print("=" * 70)

# Start asynchronous acquisition
rp_cla.runAsync(0)
print("Logic Analyzer acquisition started")
print("Waiting for CAN bus activity to trigger capture...")

# Wait for initial data acquisition
time.sleep(0.1)

# Wait for trigger (no timeout - wait indefinitely for CAN traffic)
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
output_file = "can_data.bin"
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
# PROTOCOL DECODE - Decode and display CAN frames
# ==============================================================================

print("\n" + "=" * 70)
print("DECODED CAN FRAMES")
print("=" * 70)

# Decode CAN protocol
decode = rp_cla.getDecodedData(can_decoder)
print(f"Found {len(decode)} decoded CAN events\n")

# Display each decoded event with annotation
if len(decode) > 0:
    print("Frame Details:")
    print("-" * 70)
    for index in range(len(decode)):
        annotation = rp_cla.getAnnotation(rp_la.LA_DECODER_CAN, decode[index]['control'])
        print(f"Event {index + 1}: {annotation} = {decode[index]}")
    print("-" * 70)
else:
    print("No CAN frames decoded")


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
