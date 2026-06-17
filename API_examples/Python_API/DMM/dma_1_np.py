#!/usr/bin/python3
"""
Red Pitaya DMA Acquisition Example - Basic NumPy Integration
=============================================================

This example demonstrates basic DMA (Direct Memory Access) data acquisition on Red Pitaya
using NumPy arrays for efficient data handling. It captures a fixed number of samples
from two input channels simultaneously and displays the raw ADC values.

Features:
- Dual-channel simultaneous acquisition (IN1 and IN2)
- DMA-based data transfer for efficient operation
- Trigger-based capture with configurable trigger level
- Direct data storage in NumPy arrays
- Raw 16-bit ADC value output

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Signal sources connected to IN1 and IN2
- Optional: External trigger source for precise timing

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library

Usage:
    python dma_1_np.py

Configuration:
    Modify the parameters in the CONFIGURATION section below:
    - buffer_size: Number of samples to capture per channel
    - decimation: Decimation factor (affects sample rate)
    - trigger_level: Trigger threshold in volts

Author: Red Pitaya
Date: January 2026
"""

import time
import numpy as np
import rp


# ==============================================================================
# CONFIGURATION - Set your acquisition parameters here
# ==============================================================================

# Acquisition parameters
buffer_size = 1024              # Number of samples to capture per channel
                                # Note: For larger captures, increase to ((1024 * 1024 * 128) / 2) for 128 MB
decimation = 1                  # Decimation factor (1,2,4,8,16,17,18,...,65536)
                                # RP_DEC_1 = 125 MS/s, RP_DEC_8 = 15.625 MS/s
trigger_level = 0.2             # Trigger level in volts

print("=" * 70)
print("Red Pitaya DMA Acquisition Configuration")
print("=" * 70)
print(f"Buffer size:     {buffer_size} samples per channel")
print(f"Decimation:      {decimation}")
print(f"Trigger level:   {trigger_level} V")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Prepare buffers and initialize Red Pitaya
# ==============================================================================

print("\nInitializing Red Pitaya and allocating buffers...")

# Pre-allocate NumPy arrays for data storage
# Using int16 for raw ADC values (use float32 if converting to volts)
dma_data_ch1 = np.zeros(buffer_size, dtype=np.int16)
dma_data_ch2 = np.zeros(buffer_size, dtype=np.int16)

# Initialize the Red Pitaya interface
rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# DMA MEMORY SETUP - Configure DMA memory regions
# ==============================================================================

print("\nConfiguring DMA memory regions...")

# Get available DMA memory region from FPGA
memory_region = rp.rp_AcqAxiGetMemoryRegion()
dma_start_address = memory_region[1]
dma_total_size = memory_region[2]

print(f"DMA Memory - Start: 0x{dma_start_address:X}, Size: {dma_total_size:,} bytes ({dma_total_size / (1024**2):.2f} MB)")

# Set decimation factor for the acquisition
rp.rp_AcqAxiSetDecimationFactor(decimation)

# Set trigger delay for both channels
# This defines how many samples after the trigger to capture
rp.rp_AcqAxiSetTriggerDelay(rp.RP_CH_1, buffer_size)
rp.rp_AcqAxiSetTriggerDelay(rp.RP_CH_2, buffer_size)

# Divide available memory between two channels (50% each)
channel1_start_address = dma_start_address
channel2_start_address = int(dma_start_address + (dma_total_size / 2))

# Configure buffer regions for each channel
rp.rp_AcqAxiSetBufferSamples(rp.RP_CH_1, channel1_start_address, buffer_size)
print(f"CH1 Buffer - Start: 0x{channel1_start_address:X}, "
      f"Size: {buffer_size} samples, End: 0x{channel1_start_address + buffer_size * 2:X}")

rp.rp_AcqAxiSetBufferSamples(rp.RP_CH_2, channel2_start_address, buffer_size)
print(f"CH2 Buffer - Start: 0x{channel2_start_address:X}, "
      f"Size: {buffer_size} samples, End: 0x{channel2_start_address + buffer_size * 2:X}")

# Enable DMA on both channels
rp.rp_AcqAxiEnable(rp.RP_CH_1, True)
print("DMA enabled for Channel 1")
rp.rp_AcqAxiEnable(rp.RP_CH_2, True)
print("DMA enabled for Channel 2")


# ==============================================================================
# TRIGGER CONFIGURATION - Set up acquisition trigger
# ==============================================================================

print("\nConfiguring trigger...")

# Set trigger level on Channel 1
rp.rp_AcqSetTriggerLevel(rp.RP_T_CH_1, trigger_level)
print(f"Trigger configured: Channel 1, level {trigger_level} V, positive edge")


# ==============================================================================
# DATA ACQUISITION - Start acquisition and wait for completion
# ==============================================================================

print("\nStarting acquisition...")

# Start the DMA acquisition
rp.rp_AcqStart()
print("Acquisition started - waiting for trigger...")

# Set trigger source (Channel 1 positive edge)
rp.rp_AcqSetTriggerSrc(rp.RP_TRIG_SRC_CHA_PE)

# Optional: Wait for trigger event
# Uncomment the following block to wait for the trigger before proceeding
# print("Waiting for trigger event...")
# while True:
#     trigger_state = rp.rp_AcqGetTriggerState()[1]
#     if trigger_state == rp.RP_TRIG_STATE_TRIGGERED:
#         print("Triggered!")
#         time.sleep(0.1)  # Small delay to ensure data is captured
#         break

# Wait until DMA buffers are full (data acquisition complete)
print("Waiting for DMA buffers to fill...")
fill_state = False

while not fill_state:
    fill_state = rp.rp_AcqAxiGetBufferFillState(rp.RP_CH_1)[1]

print("DMA buffers full - acquisition complete")

# Stop the acquisition
rp.rp_AcqStop()
print("Acquisition stopped")


# ==============================================================================
# DATA RETRIEVAL - Read data from DMA buffers into NumPy arrays
# ==============================================================================

print("\nRetrieving data from DMA buffers...")

# Get write pointer positions at trigger moment
write_pos_ch1 = rp.rp_AcqAxiGetWritePointerAtTrig(rp.RP_CH_1)[1]
write_pos_ch2 = rp.rp_AcqAxiGetWritePointerAtTrig(rp.RP_CH_2)[1]

print(f"Write pointer at trigger - CH1: {write_pos_ch1}, CH2: {write_pos_ch2}")

# Read data directly into NumPy arrays (use rp_AcqAxiGetDataVNP for volts)
rp.rp_AcqAxiGetDataRawNP(rp.RP_CH_1, write_pos_ch1, dma_data_ch1)
rp.rp_AcqAxiGetDataRawNP(rp.RP_CH_2, write_pos_ch2, dma_data_ch2)

print("Data retrieved successfully")


# ==============================================================================
# DATA DISPLAY - Print captured data
# ==============================================================================

print("\n" + "=" * 70)
print("CAPTURED DATA (Raw 16-bit ADC values)")
print("=" * 70)
print(f"{'N':<6} {'CH1':<18} {'CH2':<18}")
print("-" * 70)

# Display all captured samples
for i in range(buffer_size):
    print(f"{i+1:<6} {dma_data_ch1[i]:<18} {dma_data_ch2[i]:<18}")

# Display data statistics
print("\n" + "=" * 70)
print("DATA STATISTICS")
print("=" * 70)
print(f"Channel 1: Min={dma_data_ch1.min():6d}, Max={dma_data_ch1.max():6d}, "
      f"Mean={dma_data_ch1.mean():8.2f}, Std={dma_data_ch1.std():8.2f}")
print(f"Channel 2: Min={dma_data_ch2.min():6d}, Max={dma_data_ch2.max():6d}, "
      f"Mean={dma_data_ch2.mean():8.2f}, Std={dma_data_ch2.std():8.2f}")
print("=" * 70)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing resources...")

# Disable DMA on both channels
rp.rp_AcqAxiEnable(rp.RP_CH_1, False)
rp.rp_AcqAxiEnable(rp.RP_CH_2, False)

# Release Red Pitaya resources
rp.rp_Release()

print("Resources released - acquisition complete")
print("\nNote: Data is now available in 'dma_data_ch1' and 'dma_data_ch2' NumPy arrays")
print("You can process, plot, or save this data as needed.")
