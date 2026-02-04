#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - UART FPGA Loopback Example
=======================================================

This example demonstrates real-time UART protocol decoding using the Red Pitaya
Logic Analyzer in FPGA loopback mode. The script simultaneously generates UART
traffic (transmitting a test string) and captures/decodes it with the Logic
Analyzer. This is useful for verifying UART communication, testing decoder
settings, and learning UART protocol analysis.

Features:
- Real-time UART bus capture and decode from FPGA
- Loopback connection between UART peripheral and Logic Analyzer
- Test string transmission as UART traffic source
- Configurable baud rate, data bits, parity, and stop bits
- RLE (Run Length Encoding) compression for efficient storage
- Automatic protocol decoding with frame annotations
- Data export to binary file for offline analysis

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Jumper wires for loopback connections

Required Connections:
=====================
Connect the UART signals from Extension connector E2 to DIO pins on E1:
  - UART TX (E2) <-> any DIO_P pin (E1) (configured as DIO5_P in this example)
  - UART RX (E2) <-> any DIO_P pin (E1) (configured as DIO6_P in this example)

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Logic Analyzer module (rp_la)
- Red Pitaya Hardware module (rp_hw)
- NumPy library
- OS 2.00 or higher with Logic Analyzer FPGA image

Usage:
    python fpga_decode_4_uart_loop.py
    
    The program will:
    1. Load the Logic Analyzer FPGA image
    2. Configure UART to transmit test string
    3. Set up Logic Analyzer with UART decoder
    4. Start acquisition and trigger on UART activity
    5. Execute UART transmission
    6. Decode and display captured UART frames
    7. Save captured data to file

Configuration:
    Modify parameters in the CONFIGURATION sections:
    - UART baud rate, data bits, parity, and stop bits
    - Test data string
    - UART decoder pin assignments (TX/RX)
    - Logic Analyzer trigger and timing parameters
    - Decimation and sample rates

UART Parameters:
    Baud rate:  Common values: 1200, 2400, 4800, 9600, 19200, 38400, 57600, 
                115200, 230400, 460800, 921600
    Data bits:  5, 6, 7, 8, or 9 bits per frame
    Parity:     None=0, Even=1, Odd=2, Mark=3 (always 0), Space=4 (always 1)
    Stop bits:  STOP1 (1 bit), STOP2 (2 bits)

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
# CONFIGURATION - Test Data
# ==============================================================================

print("=" * 70)
print("Red Pitaya Logic Analyzer - UART FPGA Loopback Example")
print("=" * 70)

# Hardware connection reminder
print("\n!! REQUIRED HARDWARE CONNECTIONS !!")
print("Before running, connect:")
print("  - UART TX (E2) <-> DIO0_P (E1)")
print("  - UART RX (E2) <-> (Optional - set to None if not used)")
print("=" * 70)

# Test data to transmit
data = list("TEST string")
data_int = [ord(char) for char in data]     # Convert data to ASCII values
data_size = len(data_int)

print("\nTest Data Configuration:")
print(f"  Test string:    '{''.join(data)}'")
print(f"  Data size:      {data_size} bytes")
print(f"  ASCII values:   {data_int}")


# ==============================================================================
# CONFIGURATION - UART API Settings
# ==============================================================================

# UART configuration
uart_speed = 921600                         # Baud rate (1200 - 921600)
uart_timeout = 10                           # Timeout (0 - 255)
uart_word_size = rp_hw.RP_UART_CS8          # Data bits: CS6, CS7, CS8
uart_parity = rp_hw.RP_UART_MARK            # Parity: NONE, EVEN, ODD, MARK, SPACE
uart_stop_bits = rp_hw.RP_UART_STOP2        # Stop bits: STOP1, STOP2

print("\nUART Configuration:")
print(f"  Baud rate:      {uart_speed} bps")
print(f"  Timeout:        {uart_timeout}")
print(f"  Data bits:      {'8' if uart_word_size == rp_hw.RP_UART_CS8 else 'other'}")
print(f"  Parity:         {'MARK' if uart_parity == rp_hw.RP_UART_MARK else 'other'}")
print(f"  Stop bits:      {'2' if uart_stop_bits == rp_hw.RP_UART_STOP2 else '1'}")
print(f"  Data to send:   {data_size} bytes")


# ==============================================================================
# CONFIGURATION - UART Decoder Settings
# ==============================================================================

# Decoder parameters (must match UART API settings)
dec_baudrate = 921600                   # Baud rate (bits per second)
dec_bit_order = "LsbFirst"              # Bit order: "LsbFirst" or "MsbFirst"
dec_invert = "No"                       # Bit inversion: "No" = normal, "Yes" = inverted
dec_num_data_bits = "Bits8"             # Number of data bits: "Bits5", "Bits6", "Bits7", "Bits8", "Bits9"
dec_num_stop_bits = "Stop_Bit_20"       # Stop bits: "Stop_Bit_No", "Stop_Bit_05", "Stop_Bit_10", "Stop_Bit_15", "Stop_Bit_20"
dec_parity = "Always_0"                 # Parity: "None", "Even", "Odd", "Always_0", "Always_1"
dec_timeout_ms = 1000                   # Decoder timeout in milliseconds

# Pin assignments for UART signals
dec_rx = "DIN0"                         # UART RX pin: "DIN0" - "DIN7", "None" = disabled
dec_tx = "None"                         # UART TX pin: "DIN0" - "DIN7", "None" = disabled

print("\nUART Decoder Configuration:")
print(f"  Baud rate:         {dec_baudrate} bps")
print(f"  Bit order:         {dec_bit_order}")
print(f"  Invert:            {dec_invert}")
print(f"  Data bits:         {dec_num_data_bits}")
print(f"  Stop bits:         {dec_num_stop_bits}")
print(f"  Parity:            {dec_parity}")
print(f"  Timeout:           {dec_timeout_ms} ms")
print(f"  RX pin:            {dec_rx}")
print(f"  TX pin:            {dec_tx}")


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
# UART INITIALIZATION - Initialize UART and configure settings
# ==============================================================================

print("\nInitializing UART interface...")

# Initialize UART subsystem
rp_hw.rp_UartInit()
print("UART subsystem initialized")

# Configure UART parameters
rp_hw.rp_UartSetSpeed(uart_speed)
rp_hw.rp_UartSetBits(uart_word_size)
rp_hw.rp_UartSetStopBits(uart_stop_bits)
rp_hw.rp_UartSetParityMode(uart_parity)
print("UART parameters configured")

# Apply UART settings
rp_hw.rp_UartSetSettings()
print("UART settings applied to hardware")


# ==============================================================================
# DATA PREPARATION - Prepare transmit buffer
# ==============================================================================

print("\nPreparing transmit buffer...")

# Copy data to UART transmit buffer
buff_uart = rp_hw.Buffer(data_size)
for i in range(data_size):
    buff_uart[i] = data_int[i]
print(f"Transmit buffer populated with {data_size} bytes")


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
# DECODER SETUP - Add and configure UART decoder
# ==============================================================================

print("\nConfiguring UART decoder...")

# Add UART decoder
rp_cla.addDecoder("UART", rp_la.LA_DECODER_UART)

# Configure decoder settings
rp_cla.setDecoderSettingsUInt("UART", "acq_speed", acq_rate)
rp_cla.setDecoderSettingsUInt("UART", "baudrate", dec_baudrate)
rp_cla.setDecoderSettingsUInt("UART", "bitOrder", dec_bit_order)
rp_cla.setDecoderSettingsUInt("UART", "invert", dec_invert)
rp_cla.setDecoderSettingsUInt("UART", "num_data_bits", dec_num_data_bits)
rp_cla.setDecoderSettingsUInt("UART", "num_stop_bits", dec_num_stop_bits)
rp_cla.setDecoderSettingsUInt("UART", "parity", dec_parity)
rp_cla.setDecoderSettingsUInt("UART", "rx", dec_rx)
rp_cla.setDecoderSettingsUInt("UART", "tx", dec_tx)
print("UART decoder configured")


# ==============================================================================
# ACQUISITION START - Begin capturing data
# ==============================================================================

print("\n" + "=" * 70)
print("Starting Data Acquisition and UART Transmission")
print("=" * 70)

# Start asynchronous acquisition
rp_cla.runAsync(0)
print("Logic Analyzer acquisition started (waiting for trigger)")

# Wait for LA to be ready
time.sleep(0.1)

# Execute UART transaction: Transmit data
print(f"Transmitting test string: '{''.join(data)}'...")
rp_hw.rp_UartWrite(buff_uart, data_size)
print("UART transmission completed")

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
output_file = "dump_uart.bin"
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
    print("Transaction Details:")
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
