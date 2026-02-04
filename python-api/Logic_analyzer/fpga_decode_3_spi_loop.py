#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - SPI FPGA Loopback Example
======================================================

This example demonstrates real-time SPI protocol decoding using the Red Pitaya
Logic Analyzer in FPGA loopback mode. The script simultaneously generates SPI
traffic (transmitting a test string) and captures/decodes it with the Logic
Analyzer. This is useful for verifying SPI communication, testing decoder
settings, and learning SPI protocol analysis.

Features:
- Real-time SPI bus capture and decode from FPGA
- Loopback connection between SPI peripheral and Logic Analyzer
- Test string transmission as SPI traffic source
- Configurable SPI mode (LISL, LIST, HISL, HIST), bit order, and word size
- Chip Select (CS) polarity configuration
- RLE (Run Length Encoding) compression for efficient storage
- Automatic protocol decoding with MISO/MOSI annotation
- Data export to binary file for offline analysis

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Jumper wires for loopback connections

Required Connections:
=====================
Connect the SPI signals from Extension connector E2 to DIO pins on E1:
  - SPI MISO (E2) <-> any DIO_P pin (E1) (configured as DIO1_P in this example)
  - SPI MOSI (E2) <-> any DIO_P pin (E1) (configured as DIO2_P in this example)
  - SPI SCLK (E2) <-> any DIO_P pin (E1) (configured as DIO3_P in this example)
  - SPI CS   (E2) <-> any DIO_P pin (E1) (configured as DIO4_P in this example)

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Logic Analyzer module (rp_la)
- Red Pitaya Hardware module (rp_hw)
- NumPy library
- OS 2.00 or higher with Logic Analyzer FPGA image

Usage:
    python fpga_decode_3_spi_loop.py
    
    The program will:
    1. Load the Logic Analyzer FPGA image
    2. Configure SPI to transmit test string
    3. Set up Logic Analyzer with SPI decoder
    4. Start acquisition and trigger on SPI activity
    5. Execute SPI transmission
    6. Decode and display captured SPI transactions
    7. Save captured data to file

Configuration:
    Modify parameters in the CONFIGURATION sections:
    - SPI mode (LISL/LIST/HISL/HIST), CS mode, bit order, and word size
    - Test data string and transmission speed
    - SPI decoder pin assignments (MISO/MOSI/SCLK/CS)
    - Logic Analyzer trigger and timing parameters
    - Decimation and sample rates

SPI Mode Settings:
    LISL - Low idle level, sample on leading edge   (CPOL=0, CPHA=0)
    LIST - Low idle level, sample on trailing edge  (CPOL=0, CPHA=1)
    HISL - High idle level, sample on leading edge  (CPOL=1, CPHA=0)
    HIST - High idle level, sample on trailing edge (CPOL=1, CPHA=1)

Bit Order:
    MSB First = 0 (Most Significant Bit first)
    LSB First = 1 (Least Significant Bit first)

CS Mode:
    NORMAL - CS toggles for each transaction
    HIGH   - CS stays high during idle

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
print("Red Pitaya Logic Analyzer - SPI FPGA Loopback Example")
print("=" * 70)

# Hardware connection reminder
print("\n!! REQUIRED HARDWARE CONNECTIONS !!")
print("Before running, connect:")
print("  - SPI MISO (E2) <-> (Optional - set to None if not used)")
print("  - SPI MOSI (E2) <-> DIO1_P (E1)")
print("  - SPI SCLK (E2) <-> DIO0_P (E1)")
print("  - SPI CS   (E2) <-> DIO2_P (E1)")
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
# CONFIGURATION - SPI API Settings
# ==============================================================================

# SPI configuration
spi_mode = rp_hw.RP_SPI_MODE_LIST           # LISL, LIST, HISL, HIST
spi_cs_mode = rp_hw.RP_SPI_CS_NORMAL        # NORMAL, HIGH
spi_speed = 1000000                         # 1 - 100000000 Hz (1 MHz)
spi_word_size = 8                           # 7 or 8 bits
spi_bit_order = rp_hw.RP_SPI_ORDER_BIT_MSB  # MSB, LSB

msg_num = 1                                 # Number of SPI messages

print("\nSPI Configuration:")
print(f"  Mode:           {spi_mode} (LIST = CPOL=0, CPHA=1)")
print(f"  CS mode:        {'NORMAL' if spi_cs_mode == rp_hw.RP_SPI_CS_NORMAL else 'HIGH'}")
print(f"  Speed:          {spi_speed} Hz ({spi_speed/1e6:.1f} MHz)")
print(f"  Word size:      {spi_word_size} bits")
print(f"  Bit order:      {'MSB first' if spi_bit_order == rp_hw.RP_SPI_ORDER_BIT_MSB else 'LSB first'}")
print(f"  Messages:       {msg_num}")


# ==============================================================================
# CONFIGURATION - SPI Decoder Settings
# ==============================================================================

# Decoder parameters (must match SPI API settings)
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
print(f"  Bit order:         {dec_bit_order}")
print(f"  CPHA:              {dec_cpha}")
print(f"  CPOL:              {dec_cpol}")
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
# SPI INITIALIZATION - Initialize SPI and configure settings
# ==============================================================================

print("\nInitializing SPI interface...")

# Initialize SPI subsystem
rp_hw.rp_SPI_Init()
print("SPI subsystem initialized")

# Initialize SPI device
rp_hw.rp_SPI_InitDevice("/dev/spidev2.0")
print("SPI device initialized: /dev/spidev2.0")

# Configure SPI parameters
rp_hw.rp_SPI_SetMode(spi_mode)
rp_hw.rp_SPI_SetCSMode(spi_cs_mode)
rp_hw.rp_SPI_SetSpeed(spi_speed)
rp_hw.rp_SPI_SetWordLen(spi_word_size)
rp_hw.rp_SPI_SetOrderBit(spi_bit_order)
print("SPI parameters configured")

# Apply settings to SPI hardware
rp_hw.rp_SPI_SetSettings()
print("SPI settings applied")

# Reserve space for messages
rp_hw.rp_SPI_CreateMessage(msg_num)
print(f"SPI message buffer created ({msg_num} message)")


# ==============================================================================
# DATA PREPARATION - Prepare transmit buffer
# ==============================================================================

print("\nPreparing transmit buffer...")

# Copy data to SPI transmit buffer
tx_buff = rp_hw.Buffer(data_size)
for i in range(data_size):
    tx_buff[i] = data_int[i]
print(f"Transmit buffer populated with {data_size} bytes")

# Set buffer for first message and create RX buffer
#                           message number, tx_buffer, init_rx_buff,      size, toggle cs
rp_hw.rp_SPI_SetBufferForMessage(        0,  tx_buff,         True,  data_size,     False)
print("Message buffer configured (message 0)")


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
print("Starting Data Acquisition and SPI Transmission")
print("=" * 70)

# Start asynchronous acquisition
rp_cla.runAsync(0)
print("Logic Analyzer acquisition started (waiting for trigger)")

# Wait for LA to be ready
time.sleep(0.1)

# Execute SPI transaction: Transmit data
print(f"Transmitting test string: '{''.join(data)}'...")
rp_hw.rp_SPI_ReadWrite()
print("SPI transmission completed")

# Wait for trigger and acquisition to complete
print("Waiting for trigger and acquisition completion...")
res = rp_cla.wait(2000)  # Timeout: 2000 ms
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
output_file = "dump_spi.bin"
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

# Delete all SPI messages and release resources
rp_hw.rp_SPI_DestoryMessage()
print("SPI messages destroyed")

rp_hw.rp_SPI_Release()
print("SPI resources released")

# Delete controller and free resources
del rp_cla
print("Logic Analyzer resources released")

print("\nProgram completed successfully")
print("=" * 70)

# Change FPGA image to logic analyzer "logic"
fpga = overlay("logic")

# Create controller and initialize FPGA
rp_cla = rp_la.CLAController()
rp_cla.initFpga()

callback = Callback()
rp_cla.setDelegate(callback.__disown__())

# Initialize and configure SPI on Red Pitaya
rp_hw.rp_SPI_Init()
rp_hw.rp_SPI_InitDevice("/dev/spidev2.0")
rp_hw.rp_SPI_SetMode(spi_mode)
rp_hw.rp_SPI_SetCSMode(spi_cs_mode)
rp_hw.rp_SPI_SetSpeed(spi_speed)
rp_hw.rp_SPI_SetWordLen(spi_word_size)
rp_hw.rp_SPI_SetOrderBit(spi_bit_order)

# Apply settings to SPI
rp_hw.rp_SPI_SetSettings()
#print(f"Actual SPI speed: {rp_hw.rp_SPI_GetSpeed()[1]} Hz\n")

# Reserve space for messages
rp_hw.rp_SPI_CreateMessage(msg_num)

# Copy data to buffer
tx_buff = rp_hw.Buffer(data_size)
for i in range(data_size):
    tx_buff[i] = data_int[i]

# Set buffer for first message and create RX buffer
#                           message number, tx_buffer, init_rx_buff,      size, toggle cs
rp_hw.rp_SPI_SetBufferForMessage(        0,  tx_buff,         True,  data_size,     False)

# Set LA parameters
rp_cla.setEnableRLE(True)
rp_cla.setDecimation(decimation)
rp_cla.setTrigger(trigger_ch, trig_edge)
rp_cla.setPreTriggerSamples(pre_trig_samples)
rp_cla.setPostTriggerSamples(post_trig_samples)

# Add SPI decoder and configure decoder settings
rp_cla.addDecoder("SPI", rp_la.LA_DECODER_SPI)
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

# Start acquisition
rp_cla.runAsync(0)
print("Started acquire data")

time.sleep(0.1)     # Wait for LA to acquire some data

# Pass message to SPI
rp_hw.rp_SPI_ReadWrite()

# Wait for trigger
res = rp_cla.wait(2000)
if res:
    print("Exit by timeout")
    sys.exit(1)

# Save data to file
rp_cla.saveCaptureDataToFile("spi_data.bin")

# Get captured data
rawBytesCount = rp_cla.getCapturedDataSize()
raw_data = np.zeros(rawBytesCount, dtype=np.uint8)
print(f"Packed samples count: {rp_cla.getDataNP(raw_data)}")

# Get unpacked RLE data
rle_data = np.zeros(rp_cla.getCapturedSamples(), dtype=np.uint8)
print(f"Unpacked samples count: {rp_cla.getUnpackedRLEDataNP(rle_data)}")
print(f"RLE DATA {raw_data}")
print(f"UNPACKED DATA {rle_data}\n")

rp_cla.printRLE(False)

print("\nDecoded data")
decode = rp_cla.getDecodedData("SPI")
for index in range(len(decode)):
    print(f"{rp_cla.getAnnotation(rp_la.LA_DECODER_SPI, decode[index]['control'])} = {decode[index]}")

# Delete all messages and release SPI resources
rp_hw.rp_SPI_DestoryMessage()
rp_hw.rp_SPI_Release()
del rp_cla
