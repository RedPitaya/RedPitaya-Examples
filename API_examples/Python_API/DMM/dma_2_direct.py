#!/usr/bin/python3
"""
Red Pitaya DMA Acquisition Example - Direct Memory Access
==========================================================

This example demonstrates advanced DMA (Direct Memory Access) data acquisition on
Red Pitaya using direct memory buffer access without copying. It efficiently captures
large amounts of data from input channels by directly accessing the DMA memory buffers,
minimizing overhead and memory usage.

Features:
- Single-channel DMA acquisition (configurable to dual-channel)
- Zero-copy direct memory access using memory spans
- DMA-based data transfer for maximum efficiency
- Trigger-based capture with configurable trigger level
- Support for very large buffer sizes (up to 32 MB per channel)
- NumPy array views directly into memory buffers

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Signal sources connected to IN1 (and optionally IN2)

Software Requirements:
- Red Pitaya Python API (rp module)
- rp_overlay module for FPGA initialization
- NumPy library

Usage:
    python dma_2_direct.py

Configuration:
    Modify the parameters in the CONFIGURATION section below:
    - buffer_size: Number of bytes to capture (max 32 MB per channel)
    - samples: Number of samples derived from buffer size
    - decimation: Decimation factor (affects sample rate)
    - trigger_level: Trigger threshold in volts
    - trigger_delay: Number of samples after trigger to capture

Important:
    This example uses rp_AcqAxiGetDataRawDirect() which returns memory spans
    that directly reference the DMA buffers without copying data. This is the
    most efficient method for large data captures.

Author: Red Pitaya
Date: January 2026
"""

import time
import numpy as np
from rp_overlay import overlay
import rp


# ==============================================================================
# CONFIGURATION - Set your acquisition parameters here
# ==============================================================================

# Buffer configuration
buffer_size = 1024 * 1024 * 32  # 32 MB buffer (maximum size)
samples = int(buffer_size / 2)   # Number of samples (2 bytes per sample)

# Acquisition parameters
decimation = rp.RP_DEC_1        # Decimation factor: RP_DEC_1 = 125 MS/s
trigger_level = 0               # Trigger level in volts
trigger_delay_samples = samples  # Capture this many samples after trigger

print("=" * 70)
print("Red Pitaya DMA Direct Memory Access Configuration")
print("=" * 70)
print(f"Buffer size:       {buffer_size:,} bytes ({buffer_size / (1024**2):.2f} MB)")
print(f"Samples:           {samples:,} samples")
print(f"Decimation:        {decimation}")
print(f"Trigger level:     {trigger_level} V")
print(f"Trigger delay:     {trigger_delay_samples:,} samples")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize FPGA overlay and Red Pitaya
# ==============================================================================

print("\nInitializing FPGA overlay and Red Pitaya...")

# Initialize FPGA overlay
fpga = overlay()
print("FPGA overlay loaded")

# Optional: Enable debug register for troubleshooting
# rp.rp_EnableDebugReg()

# Initialize the Red Pitaya interface
rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# DMA MEMORY SETUP - Configure DMA memory regions
# ==============================================================================

print("\nConfiguring DMA memory regions...")

# Get available DMA memory region from FPGA
memory = rp.rp_AcqAxiGetMemoryRegion()

# Check if memory region access was successful
if memory[0] != rp.RP_OK:
    print("ERROR: Failed to access reserved DMA memory")
    print("Make sure the Red Pitaya FPGA is properly configured")
    exit(1)

dma_start_address = memory[1]
dma_full_size = memory[2]

print(f"DMA Memory - Start: 0x{dma_start_address:X}, Size: {dma_full_size:,} bytes ({dma_full_size / (1024**2):.2f} MB)")

# Adjust buffer size if requested size exceeds available DMA memory
if dma_full_size < buffer_size:
    buffer_size = dma_full_size
    samples = int(buffer_size / 2)
    print("Warning: Requested buffer size exceeds available memory")
    print(f"Adjusted to: {buffer_size:,} bytes ({samples:,} samples)")


# ==============================================================================
# ACQUISITION CONFIGURATION - Set up DMA acquisition
# ==============================================================================

print("\nConfiguring acquisition parameters...")

# Set Decimation factor
rp.rp_AcqAxiSetDecimationFactor(decimation)
print(f"Decimation set to: {decimation}")

# Set trigger level and delay
rp.rp_AcqSetTriggerLevel(rp.RP_T_CH_1, trigger_level)
print(f"Trigger level: {trigger_level} V on Channel 1")

rp.rp_AcqAxiSetTriggerDelay(rp.RP_CH_1, trigger_delay_samples)
print(f"Trigger delay: {trigger_delay_samples:,} samples")

# Configure buffer for Channel 1
rp.rp_AcqAxiSetBufferSamples(rp.RP_CH_1, dma_start_address, samples)
print(f"CH1 Buffer - Start: 0x{dma_start_address:X}, Size: {samples:,} samples")

# Enable DMA on Channel 1
rp.rp_AcqAxiEnable(rp.RP_CH_1, True)
print("DMA enabled for Channel 1")


# ==============================================================================
# DATA ACQUISITION - Start acquisition and wait for completion
# ==============================================================================

print("\n" + "=" * 70)
print("Starting Data Acquisition")
print("=" * 70)

# Start Acquisition
rp.rp_AcqStart()
print("Acquisition started - waiting for trigger...")

# Small delay to ensure acquisition is ready
time.sleep(0.1)

# Trigger immediately (use RP_TRIG_SRC_CHA_PE for external trigger)
rp.rp_AcqSetTriggerSrc(rp.RP_TRIG_SRC_NOW)
print("Trigger source set: NOW (immediate trigger)")

time.sleep(0.1)

# Wait for trigger event
print("\nWaiting for trigger state...")
while True:
    trig_state = rp.rp_AcqGetTriggerState()[1]
    if trig_state == rp.RP_TRIG_STATE_TRIGGERED:
        print("Triggered!")
        break

# Wait until DMA buffer is full (data acquisition complete)
print("Waiting for DMA buffer to fill...")
while True:
    fill_state = rp.rp_AcqAxiGetBufferFillState(rp.RP_CH_1)[1]
    if fill_state:
        print("DMA buffer full - acquisition complete")
        break


# ==============================================================================
# DATA RETRIEVAL - Direct memory access (zero-copy)
# ==============================================================================

print("\n" + "=" * 70)
print("Retrieving Data via Direct Memory Access")
print("=" * 70)

# Get write pointer position at trigger moment
write_pointer_at_trigger = rp.rp_AcqAxiGetWritePointerAtTrig(rp.RP_CH_1)[1]
print(f"Write pointer at trigger: {write_pointer_at_trigger:,}")

# Get data using direct memory access (returns memory spans without copying)
print("\nAccessing DMA memory directly (zero-copy)...")
result = rp.rp_AcqAxiGetDataRawDirect(rp.RP_CH_1, write_pointer_at_trigger, samples)

# Check if data retrieval was successful
if result[0] != rp.RP_OK:
    print("ERROR: Failed to retrieve data from DMA buffer")
    rp.rp_Release()
    exit(1)

# Convert memory spans to NumPy arrays
# Note: Each span is a memory buffer view - no data is copied
arrays = []
for span in result[1]:
    arr = np.frombuffer(span, dtype=np.int16)
    arrays.append(arr)

print(f"Retrieved {len(arrays)} memory span(s)")
total_samples = sum(len(arr) for arr in arrays)
print(f"Total samples retrieved: {total_samples:,}")


# ==============================================================================
# DATA DISPLAY - Show sample data and statistics
# ==============================================================================

print("\n" + "=" * 70)
print("DATA SAMPLE (First 20 samples from each span)")
print("=" * 70)

for span_idx, arr in enumerate(arrays):
    print(f"\nSpan {span_idx + 1}: {len(arr):,} samples")
    print(f"{'Sample':<8} {'Value (raw)':<12} {'Index':<8}")
    print("-" * 32)
    
    # Display first 20 samples from this span
    display_count = min(20, len(arr))
    for i in range(display_count):
        print(f"{i+1:<8} {arr[i]:<12} {i:<8}")
    
    if len(arr) > 20:
        print(f"... ({len(arr) - 20:,} more samples)")

print("\n" + "=" * 70)
print("DATA STATISTICS")
print("=" * 70)

for span_idx, arr in enumerate(arrays):
    print(f"Span {span_idx + 1}:")
    print(f"  Samples: {len(arr):,}")
    print(f"  Min:     {arr.min():6d}")
    print(f"  Max:     {arr.max():6d}")
    print(f"  Mean:    {arr.mean():8.2f}")
    print(f"  Std:     {arr.std():8.2f}")

print("=" * 70)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing resources...")

# Disable DMA on both channels
rp.rp_AcqAxiEnable(rp.RP_CH_1, False)
rp.rp_AcqAxiEnable(rp.RP_CH_2, False)
print("DMA disabled")

# Release Red Pitaya resources
rp.rp_Release()
print("Resources released - acquisition complete")

print("\n" + "=" * 70)
print("Note: Data is available in 'arrays' list as NumPy array views")
print("These arrays directly reference DMA memory (zero-copy).")
print("Process or save this data before the program exits.")
print("=" * 70)

