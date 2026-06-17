#!/usr/bin/python3
"""
Red Pitaya DMA Acquisition Example - File Output
=================================================

This example demonstrates how to save DMA-acquired data to a file using the
recommended NumPy method (rp_AcqAxiGetDataRawWithCalibNP). It acquires data
from two channels simultaneously and writes the results to a text file.

For a pure acquisition example without file output, see dma_1_np.py.
For the legacy chunked approach, see dma_6_basic.py.

Features:
- Dual-channel simultaneous acquisition (IN1 and IN2)
- NumPy-based data retrieval (single copy, no chunking)
- Trigger-based capture with configurable trigger level
- Text file output with sample index, CH1 and CH2 values
- Optional voltage conversion before saving

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Signal sources connected to IN1 and IN2

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library

Usage:
    python dma_5_file.py

Output:
    Creates 'out.txt' with captured data in the format:
    Sample_Number:  CH1_Value    CH2_Value

Configuration:
    Modify the parameters in the CONFIGURATION section below:
    - buffer_size: Number of samples to capture per channel
    - decimation: Decimation factor (affects sample rate)
    - trigger_level: Trigger threshold in volts
    - output_filename: Output file name

Author: Red Pitaya
Date: May 2026
"""

import time
import numpy as np
import rp


# ==============================================================================
# CONFIGURATION - Set your acquisition parameters here
# ==============================================================================

buffer_size      = 1024         # Number of samples to capture per channel
decimation       = 1            # Decimation factor (1 = 125 MS/s, 8 = 15.625 MS/s)
trigger_level    = 0.2          # Trigger level in volts
output_filename  = "out.txt"    # Output file name

print("=" * 70)
print("Red Pitaya DMA Acquisition - File Output")
print("=" * 70)
print(f"Buffer size:     {buffer_size} samples per channel")
print(f"Decimation:      {decimation}")
print(f"Trigger level:   {trigger_level} V")
print(f"Output file:     {output_filename}")
print("=" * 70)


# ==============================================================================
# INITIALIZATION
# ==============================================================================

print("\nInitializing Red Pitaya and allocating buffers...")

dma_data_ch1 = np.zeros(buffer_size, dtype=np.int16)
dma_data_ch2 = np.zeros(buffer_size, dtype=np.int16)

rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# DMA MEMORY SETUP
# ==============================================================================

print("\nConfiguring DMA memory regions...")

memory_region = rp.rp_AcqAxiGetMemoryRegion()
dma_start_address = memory_region[1]
dma_total_size    = memory_region[2]

print(f"DMA Memory - Start: 0x{dma_start_address:X}, Size: {dma_total_size:,} bytes ({dma_total_size / (1024**2):.2f} MB)")

rp.rp_AcqAxiSetDecimationFactor(decimation)
rp.rp_AcqAxiSetTriggerDelay(rp.RP_CH_1, buffer_size)
rp.rp_AcqAxiSetTriggerDelay(rp.RP_CH_2, buffer_size)

channel1_start_address = dma_start_address
channel2_start_address = int(dma_start_address + (dma_total_size / 2))

rp.rp_AcqAxiSetBufferSamples(rp.RP_CH_1, channel1_start_address, buffer_size)
rp.rp_AcqAxiSetBufferSamples(rp.RP_CH_2, channel2_start_address, buffer_size)

rp.rp_AcqAxiEnable(rp.RP_CH_1, True)
rp.rp_AcqAxiEnable(rp.RP_CH_2, True)
print(f"CH1 Buffer - Start: 0x{channel1_start_address:X}, Size: {buffer_size} samples")
print(f"CH2 Buffer - Start: 0x{channel2_start_address:X}, Size: {buffer_size} samples")


# ==============================================================================
# TRIGGER CONFIGURATION
# ==============================================================================

print("\nConfiguring trigger...")
rp.rp_AcqSetTriggerLevel(rp.RP_T_CH_1, trigger_level)
print(f"Trigger: Channel 1, level {trigger_level} V, positive edge")


# ==============================================================================
# DATA ACQUISITION
# ==============================================================================

print("\nStarting acquisition...")
rp.rp_AcqStart()
rp.rp_AcqSetTriggerSrc(rp.RP_TRIG_SRC_CHA_PE)
print("Waiting for DMA buffers to fill...")

fill_state = False
while not fill_state:
    fill_state = rp.rp_AcqAxiGetBufferFillState(rp.RP_CH_1)[1]

rp.rp_AcqStop()
print("Acquisition complete")


# ==============================================================================
# DATA RETRIEVAL
# ==============================================================================

print("\nRetrieving data from DMA buffers...")

write_pos_ch1 = rp.rp_AcqAxiGetWritePointerAtTrig(rp.RP_CH_1)[1]
write_pos_ch2 = rp.rp_AcqAxiGetWritePointerAtTrig(rp.RP_CH_2)[1]

rp.rp_AcqAxiGetDataRawNP(rp.RP_CH_1, write_pos_ch1, dma_data_ch1)
rp.rp_AcqAxiGetDataRawNP(rp.RP_CH_2, write_pos_ch2, dma_data_ch2)

print("Data retrieved successfully")


# ==============================================================================
# FILE OUTPUT
# ==============================================================================

print(f"\nWriting {buffer_size} samples to '{output_filename}'...")

with open(output_filename, "w", encoding="ascii") as f:
    f.write("# Red Pitaya DMA Acquisition\n")
    f.write(f"# Samples: {buffer_size}, Decimation: {decimation}, Trigger: {trigger_level} V\n")
    f.write(f"# {'N':<6}  {'CH1':>8}  {'CH2':>8}\n")
    for i in range(buffer_size):
        f.write(f"  {i + 1:<6}  {dma_data_ch1[i]:>8}  {dma_data_ch2[i]:>8}\n")

print(f"Data saved to '{output_filename}'")
print("Format: sample index, CH1 raw int16, CH2 raw int16")


# ==============================================================================
# CLEANUP
# ==============================================================================

print("\nReleasing resources...")
rp.rp_AcqAxiEnable(rp.RP_CH_1, False)
rp.rp_AcqAxiEnable(rp.RP_CH_2, False)
rp.rp_Release()
print("Done")
