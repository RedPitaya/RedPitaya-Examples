#!/usr/bin/python3
"""
Red Pitaya DMA Acquisition Example - Basic (Legacy) Method
===========================================================

This example demonstrates DMA data acquisition using the basic chunked read
approach with rp.i16Buffer and rp_AcqAxiGetDataRaw(). This is the simplest
method conceptually, but it involves multiple intermediate buffer copies and
is significantly slower than the NumPy (dma_1_np.py) or Direct (dma_2_direct.py)
approaches.

It is kept as a reference to illustrate what the faster methods improve upon.
For new code, prefer dma_1_np.py (NumPy) or dma_2_direct.py (zero-copy direct).

Features:
- Dual-channel simultaneous acquisition (IN1 and IN2)
- Chunked data reading with rp.i16Buffer
- File output of captured data

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Signal sources connected to IN1 and IN2

Software Requirements:
- Red Pitaya Python API (rp module)

Usage:
    python dma_6_basic.py

Output:
    Creates 'out.txt' file with captured data in the format:
    Sample_Number:  CH1_Value    CH2_Value

Author: Red Pitaya
Date: January 2026
"""

import time
import rp


# ==============================================================================
# CONFIGURATION - Set your acquisition parameters here
# ==============================================================================

# Acquisition parameters
data_size = 1024                # Total samples to capture per channel
                                # Note: For larger captures, increase to ((1024 * 1024 * 128) / 2) for 128 MB
read_chunk_size = 1024          # Number of samples to read per iteration
                                # For large captures, use (1024 * 256) to read in chunks
decimation = 1                  # Decimation factor (1,2,4,8,16,17,18,...,65536)
                                # 1 = 125 MS/s, 8 = 15.625 MS/s
trigger_level = 0.2             # Trigger level in volts
output_filename = "out.txt"     # Output file name

print("=" * 70)
print("Red Pitaya DMA Acquisition Configuration - File Output")
print("=" * 70)
print(f"Total data size:     {data_size} samples per channel")
print(f"Read chunk size:     {read_chunk_size} samples")
print(f"Decimation:          {decimation}")
print(f"Trigger level:       {trigger_level} V")
print(f"Output file:         {output_filename}")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya
# ==============================================================================

print("\nInitializing Red Pitaya...")

# Initialize the Red Pitaya interface
rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# DMA MEMORY SETUP - Configure DMA memory regions
# ==============================================================================

print("\nConfiguring DMA memory regions...")

# Get available DMA memory region from FPGA
memory_region = rp.rp_AcqAxiGetMemoryRegion()

# Check if memory region access was successful
if memory_region[0] != rp.RP_OK:
    print("ERROR: Failed to access reserved DMA memory")
    print("Make sure the Red Pitaya FPGA is properly configured")
    exit(1)

dma_start_address = memory_region[1]
dma_total_size = memory_region[2]

print(f"DMA Memory - Start: 0x{dma_start_address:X}, Size: {dma_total_size:,} bytes ({dma_total_size / (1024**2):.2f} MB)")

# Set decimation factor for the acquisition
rp.rp_AcqAxiSetDecimationFactor(decimation)

# Set trigger delay for both channels
# This defines how many samples after the trigger to capture
rp.rp_AcqAxiSetTriggerDelay(rp.RP_CH_1, data_size)
rp.rp_AcqAxiSetTriggerDelay(rp.RP_CH_2, data_size)

# Divide available memory between two channels (50% each)
channel1_start_address = dma_start_address
channel2_start_address = int(dma_start_address + (dma_total_size / 2))

# Configure buffer regions for each channel
rp.rp_AcqAxiSetBufferSamples(rp.RP_CH_1, channel1_start_address, data_size)
rp.rp_AcqAxiSetBufferSamples(rp.RP_CH_2, channel2_start_address, data_size)

print(f"CH1 Buffer - Start: 0x{channel1_start_address:X}, Size: {data_size} samples")
print(f"CH2 Buffer - Start: 0x{channel2_start_address:X}, Size: {data_size} samples")

# Enable DMA on both channels
rp.rp_AcqAxiEnable(rp.RP_CH_1, True)
rp.rp_AcqAxiEnable(rp.RP_CH_2, True)
print("DMA enabled for both channels")


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

# Wait for trigger event
print("Waiting for trigger event...")
while True:
    trigger_state = rp.rp_AcqGetTriggerState()[1]
    if trigger_state == rp.RP_TRIG_STATE_TRIGGERED:
        print("Triggered!")
        time.sleep(1)  # Wait for data to be captured after trigger
        break

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
# DATA RETRIEVAL - Read data from DMA buffers and save to file
# ==============================================================================

print("\nRetrieving data from DMA buffers...")

# Get write pointer positions at trigger moment
write_pos_ch1 = rp.rp_AcqAxiGetWritePointerAtTrig(rp.RP_CH_1)[1]
write_pos_ch2 = rp.rp_AcqAxiGetWritePointerAtTrig(rp.RP_CH_2)[1]

print(f"Write pointer at trigger - CH1: {write_pos_ch1}, CH2: {write_pos_ch2}")

# Allocate memory buffers for reading data in chunks (use fBuffer for volts)
buffer_ch1 = rp.i16Buffer(read_chunk_size)
buffer_ch2 = rp.i16Buffer(read_chunk_size)

print(f"\nWriting data to '{output_filename}'...")

# Write data to file in chunks
with open(output_filename, "w", encoding="ascii") as file:
    samples_read = 0
    
    while samples_read < data_size:
        # Calculate how many samples to read this iteration
        samples_to_read = min(read_chunk_size, data_size - samples_read)
        
        # Read data from both channels (use rp_AcqAxiGetDataV for volts)
        rp.rp_AcqAxiGetDataRaw(rp.RP_CH_1, write_pos_ch1, samples_to_read, buffer_ch1.cast())
        rp.rp_AcqAxiGetDataRaw(rp.RP_CH_2, write_pos_ch2, samples_to_read, buffer_ch2.cast())
        
        # Write data to file
        for i in range(samples_to_read):
            file.write(f"{samples_read + i + 1:6d}:  {buffer_ch1[i]:6d}\t{buffer_ch2[i]:6d}\n")
        
        # Update positions and counters
        write_pos_ch1 += samples_to_read
        write_pos_ch2 += samples_to_read
        samples_read += samples_to_read
        
        print(f"Saved {samples_read}/{data_size} samples ({samples_read/data_size*100:.1f}%)")

print(f"\nData successfully saved to '{output_filename}'")


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
print(f"\nCaptured data is available in '{output_filename}'")
print("Format: Sample_Number:  CH1_Value    CH2_Value")
