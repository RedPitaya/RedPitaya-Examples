#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - UART External Signal Decoder
=========================================================

This example demonstrates real-time UART protocol decoding using the Red Pitaya
Logic Analyzer capturing external UART signals. The script configures the Logic
Analyzer to trigger on UART activity, capture serial data, and automatically
decode UART frames including start bits, data bits, parity, and stop bits.

Features:
- Real-time UART capture from external signals
- Configurable baud rates (1200 to 921600 bps)
- Support for 5, 6, 7, 8, or 9 data bits
- Multiple parity options (None, Even, Odd, Mark, Space)
- Configurable stop bits (0.5, 1.0, 1.5, or 2.0)
- Bit order configuration (LSB-first or MSB-first)
- Automatic frame detection and validation
- Parity error detection
- RLE (Run Length Encoding) compression for efficient storage
- Detailed protocol annotations for each decoded element
- Data export to binary file for offline analysis

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- External UART device or serial bus with active traffic

Required Connections:
=====================
Connect external UART signals to Red Pitaya DIO pins on Extension connector E1:
  - UART RX signal <-> DIO5_P (E1) (or any other DIO_P pin, configurable)
  - UART TX signal <-> DIO6_P (E1) (or any other DIO_P pin, configurable)

Note: UART signals are typically 3.3V or 5V logic levels. Ensure voltage
compatibility with Red Pitaya DIO pins (3.3V tolerant).

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Logic Analyzer module (rp_la)
- NumPy library
- OS 2.00 or higher with Logic Analyzer FPGA image

Usage:
    python la_decode_4_uart_fpga.py
    
    The program will:
    1. Load the Logic Analyzer FPGA image
    2. Configure UART decoder with baud rate and frame format
    3. Set up Logic Analyzer trigger and acquisition
    4. Wait for UART activity to trigger capture
    5. Decode captured UART frames
    6. Display decoded protocol elements
    7. Save captured data to file

Configuration:
    Modify parameters in the CONFIGURATION sections:
    - Baud rate (1200 to 921600 bps)
    - Data bits (5, 6, 7, 8, or 9)
    - Parity (None, Even, Odd, Mark/Always_0, Space/Always_1)
    - Stop bits (0.5, 1.0, 1.5, or 2.0)
    - Bit order (LSB-first or MSB-first)
    - RX and TX pin assignments
    - Logic Analyzer trigger and timing parameters
    - Decimation and sample rates

UART Parameters:
    Common baud rates: 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600
    Standard format: 8 data bits, no parity, 1 stop bit (8N1)

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
# CONFIGURATION - UART Decoder Settings
# ==============================================================================

print("=" * 70)
print("Red Pitaya Logic Analyzer - UART External Signal Decoder")
print("=" * 70)

# Hardware connection reminder
print("\n!! REQUIRED HARDWARE CONNECTIONS !!")
print("Before running, connect:")
print("  - External UART RX signal <-> DIO0_P (E1)")
print("  - External UART TX signal <-> (Optional - set to None if not used)")
print("  (Ensure voltage levels are compatible with 3.3V logic)")
print("=" * 70)

# UART decoder configuration
baudrate = 921600                       # Baud rate (1200-921600 bps)
bit_order = "LsbFirst"                  # Bit order: "LsbFirst" or "MsbFirst"
invert = "No"                           # Bit inversion: "No" = normal, "Yes" = inverted
num_data_bits = "Bits8"                 # Number of data bits: "Bits5", "Bits6", "Bits7", "Bits8", "Bits9"
num_stop_bits = "Stop_Bit_10"           # Stop bits: "Stop_Bit_No", "Stop_Bit_05", "Stop_Bit_10", "Stop_Bit_15", "Stop_Bit_20"
parity = "None"                         # Parity: "None", "Even", "Odd", "Always_0", "Always_1"

# Pin assignments for UART signals
rx_line = "DIN0"                        # UART RX pin: "DIN0" - "DIN7", "None" = disabled
tx_line = "None"                        # UART TX pin: "DIN0" - "DIN7", "None" = disabled

print("\nUART Decoder Configuration:")
print(f"  Baud rate:         {baudrate} bps")
print(f"  Bit order:         {bit_order}")
print(f"  Invert:            {invert}")
print(f"  Data bits:         {num_data_bits}")
print(f"  Stop bits:         {num_stop_bits}")
print(f"  Parity:            {parity}")
print(f"  RX pin:            {rx_line}")
print(f"  TX pin:            {tx_line}")


# ==============================================================================
# CONFIGURATION - Logic Analyzer Acquisition
# ==============================================================================

trigger_ch = rp_la.LA_T_CHANNEL_5       # Trigger on channel 5 (RX)
trig_edge = rp_la.LA_RISING_OR_FALLING  # Trigger on any edge

enable_RLE = True                       # Enable RLE compression
decimation = 16                         # Decimation factor
acq_rate = int(rp_hw_profiles.rp_HPGetBaseSpeedHzOrDefault() / decimation)
pre_trig_samples = int(125e6/decimation * 1e-3)   # 1 ms pre-trigger
post_trig_samples = int(125e6/decimation * 3e-3)  # 3 ms post-trigger

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
rp_cla.setEnableRLE(enable_RLE)
rp_cla.setDecimation(decimation)
rp_cla.setTrigger(trigger_ch, trig_edge)
rp_cla.setPreTriggerSamples(pre_trig_samples)
rp_cla.setPostTriggerSamples(post_trig_samples)
print("Acquisition parameters configured")


# ==============================================================================
# DECODER SETUP - Add and configure UART decoder
# ==============================================================================

print("\nConfiguring UART decoder...")

# Add UART decoder
rp_cla.addDecoder("UART", rp_la.LA_DECODER_UART)

# Configure decoder settings
rp_cla.setDecoderSettingsUInt("UART", "acq_speed", acq_rate)
rp_cla.setDecoderSettingsUInt("UART", "baudrate", baudrate)
rp_cla.setDecoderSettingsUInt("UART", "bitOrder", bit_order)
rp_cla.setDecoderSettingsUInt("UART", "invert", invert)
rp_cla.setDecoderSettingsUInt("UART", "num_data_bits", num_data_bits)
rp_cla.setDecoderSettingsUInt("UART", "num_stop_bits", num_stop_bits)
rp_cla.setDecoderSettingsUInt("UART", "parity", parity)
rp_cla.setDecoderSettingsUInt("UART", "rx", rx_line)
rp_cla.setDecoderSettingsUInt("UART", "tx", tx_line)
print("UART decoder configured")


# ==============================================================================
# ACQUISITION START - Begin capturing data
# ==============================================================================

print("\n" + "=" * 70)
print("Starting Data Acquisition")
print("=" * 70)

# Start asynchronous acquisition
rp_cla.runAsync(0)
print("Logic Analyzer acquisition started")
print("Waiting for UART activity to trigger capture...")

# Wait for initial data acquisition
time.sleep(0.1)

# Wait for trigger (no timeout - wait indefinitely for UART traffic)
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
output_file = "uart_data.bin"
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
# PROTOCOL DECODE - Decode and display UART frames
# ==============================================================================

print("\n" + "=" * 70)
print("DECODED UART FRAMES")
print("=" * 70)

# Decode UART protocol
decode = rp_cla.getDecodedData("UART")
print(f"Found {len(decode)} decoded UART events\n")

# Display each decoded event with annotation
if len(decode) > 0:
    print("Frame Details:")
    print("-" * 70)
    for index in range(len(decode)):
        annotation = rp_cla.getAnnotation(rp_la.LA_DECODER_UART, decode[index]['control'])
        print(f"Event {index + 1}: {annotation} = {decode[index]}")
    print("-" * 70)
else:
    print("No UART frames decoded")


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
