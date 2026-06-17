#!/usr/bin/python3
"""
Red Pitaya DMA Acquisition Performance Comparison
==================================================

This example demonstrates and compares different methods of retrieving DMA data
from Red Pitaya. It benchmarks three data retrieval approaches to help users
choose the most efficient method for their application.

Methods Compared:
1. rp_AcqAxiGetDataRawNP()    - Raw int16 data with NumPy array copy
2. rp_AcqAxiGetDataVNP()       - Voltage data with conversion and NumPy array copy
3. rp_AcqAxiGetDataRawDirect() - Direct memory access without data copy (fastest)

Features:
- Performance benchmarking of different data retrieval methods
- Single-channel high-speed acquisition
- Memory-efficient direct access option
- Timing measurements for each method

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Signal source connected to IN1

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- rp_overlay module

Usage:
    python dma_3_comparison.py

Output:
    Displays execution time for each method and sample data

Note:
    The direct memory access method (method 3) is the fastest but returns
    memory views that may be invalidated after subsequent API calls. Copy
    the data if you need to retain it.

Author: Red Pitaya
"""

import time
import numpy as np
from rp_overlay import overlay
import rp


# ==============================================================================
# CONFIGURATION - Set your acquisition parameters here
# ==============================================================================

# Acquisition parameters
buffer_size_bytes = 1024 * 1024 * 32  # 32 MB buffer size
samples_to_capture = buffer_size_bytes // 2  # int16 = 2 bytes per sample

decimation = rp.RP_DEC_1        # Decimation factor (RP_DEC_1 = 125 MS/s)
trigger_level = 0.0             # Trigger level in volts
trigger_delay = samples_to_capture  # Capture all samples after trigger

print("=" * 70)
print("Red Pitaya DMA Performance Comparison")
print("=" * 70)
print(f"Buffer size:     {buffer_size_bytes / (1024**2):.1f} MB")
print(f"Samples:         {samples_to_capture:,}")
print(f"Decimation:      {decimation} (125 MS/s)")
print(f"Trigger:         {trigger_level} V")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya and FPGA
# ==============================================================================

print("\nInitializing Red Pitaya...")

# Initialize FPGA overlay
fpga = overlay()

# Uncomment to enable debug registers if needed
# rp.rp_EnableDebugReg()

# Initialize Red Pitaya API
rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# DMA MEMORY SETUP - Configure DMA memory region
# ==============================================================================

print("\nConfiguring DMA memory...")

# Get available DMA memory region
memory = rp.rp_AcqAxiGetMemoryRegion()
if memory[0] != rp.RP_OK:
    print("ERROR: Failed to get reserved DMA memory")
    print("Make sure the Red Pitaya FPGA is properly configured")
    exit(1)

dma_start_address = memory[1]
dma_full_size = memory[2]

print(f"DMA Memory - Start: 0x{dma_start_address:X}, Size: {dma_full_size:,} bytes ({dma_full_size / (1024**2):.1f} MB)")

# Adjust buffer size if DMA memory is smaller than requested
if dma_full_size < buffer_size_bytes:
    buffer_size_bytes = dma_full_size
    samples_to_capture = buffer_size_bytes // 2
    print(f"Adjusted buffer to available memory: {samples_to_capture:,} samples")


# ==============================================================================
# ACQUISITION CONFIGURATION - Set up acquisition parameters
# ==============================================================================

print("\nConfiguring acquisition...")

# Set decimation factor
rp.rp_AcqAxiSetDecimationFactor(decimation)

# Set trigger parameters
rp.rp_AcqSetTriggerLevel(rp.RP_T_CH_1, trigger_level)
rp.rp_AcqAxiSetTriggerDelay(rp.RP_CH_1, trigger_delay)

# Configure buffer for Channel 1
rp.rp_AcqAxiSetBufferSamples(rp.RP_CH_1, dma_start_address, samples_to_capture)

# Enable DMA for Channel 1
rp.rp_AcqAxiEnable(rp.RP_CH_1, True)
print("Channel 1 configured and enabled")


# ==============================================================================
# DATA ACQUISITION - Start acquisition and wait for trigger
# ==============================================================================

print("\nStarting acquisition...")

# Start acquisition
rp.rp_AcqStart()
print("Acquisition started")

# Small delay for stability
time.sleep(0.1)

# Trigger immediately (no external trigger required for this test)
rp.rp_AcqSetTriggerSrc(rp.RP_TRIG_SRC_NOW)
time.sleep(0.1)

# Wait for trigger
print("Waiting for trigger...")
while True:
    trigger_state = rp.rp_AcqGetTriggerState()[1]
    if trigger_state == rp.RP_TRIG_STATE_TRIGGERED:
        print("Triggered!")
        break

# Wait for buffer to fill
print("Waiting for buffer to fill...")
while True:
    if rp.rp_AcqAxiGetBufferFillState(rp.RP_CH_1)[1]:
        print("Buffer full - acquisition complete")
        break

# Get write pointer position at trigger
write_pointer = rp.rp_AcqAxiGetWritePointerAtTrig(rp.RP_CH_1)[1]
print(f"Write pointer at trigger: {write_pointer}")


# ==============================================================================
# PERFORMANCE COMPARISON - Test different data retrieval methods
# ==============================================================================

print("\n" + "=" * 70)
print("PERFORMANCE COMPARISON - Data Retrieval Methods")
print("=" * 70)

# Pre-allocate arrays for methods 1 and 2
raw_data_array = np.zeros(samples_to_capture, dtype=np.int16)
voltage_data_array = np.zeros(samples_to_capture, dtype=np.float32)

print("\nMethod 1: Raw int16 data with NumPy copy (rp_AcqAxiGetDataRawNP)")
print("-" * 70)
start_time = time.time()
result = rp.rp_AcqAxiGetDataRawNP(rp.RP_CH_1, write_pointer, raw_data_array)
end_time_1 = time.time()
elapsed_1 = end_time_1 - start_time
print(f"Time elapsed: {elapsed_1:.6f} seconds")
print(f"Data rate:    {samples_to_capture * 2 / elapsed_1 / (1024**2):.2f} MB/s")
print(f"Sample data:  {raw_data_array[:10]} ...")

print("\nMethod 2: Voltage data with conversion (rp_AcqAxiGetDataVNP)")
print("-" * 70)
start_time_2 = time.time()
result = rp.rp_AcqAxiGetDataVNP(rp.RP_CH_1, write_pointer, voltage_data_array)
end_time_2 = time.time()
elapsed_2 = end_time_2 - start_time_2
print(f"Time elapsed: {elapsed_2:.6f} seconds")
print(f"Data rate:    {samples_to_capture * 4 / elapsed_2 / (1024**2):.2f} MB/s")
print(f"Sample data:  {voltage_data_array[:10]} ...")

print("\nMethod 3: Direct memory access - no copy (rp_AcqAxiGetDataRawDirect)")
print("-" * 70)
start_time_3 = time.time()
result = rp.rp_AcqAxiGetDataRawDirect(rp.RP_CH_1, write_pointer, samples_to_capture)
end_time_3 = time.time()
elapsed_3 = end_time_3 - start_time_3

# Convert memory spans to NumPy arrays (this is where copying happens if needed)
direct_arrays = []
for memory_span in result[1]:
    arr = np.frombuffer(memory_span, dtype=np.int16)
    direct_arrays.append(arr)

print(f"Time elapsed: {elapsed_3:.6f} seconds (just pointer access)")
print(f"Memory spans: {len(direct_arrays)}")
print(f"Sample data:  {direct_arrays[0][:10] if direct_arrays else 'No data'} ...")


# ==============================================================================
# RESULTS SUMMARY - Compare performance
# ==============================================================================

print("\n" + "=" * 70)
print("PERFORMANCE SUMMARY")
print("=" * 70)
print(f"Method 1 (Raw NumPy):      {elapsed_1:.6f} seconds")
print(f"Method 2 (Voltage NumPy):  {elapsed_2:.6f} seconds")
print(f"Method 3 (Direct Access):  {elapsed_3:.6f} seconds")
print("-" * 70)

fastest = min(elapsed_1, elapsed_2, elapsed_3)
print(f"Method 1 speedup vs fastest: {elapsed_1/fastest:.2f}x")
print(f"Method 2 speedup vs fastest: {elapsed_2/fastest:.2f}x")
print(f"Method 3 speedup vs fastest: {elapsed_3/fastest:.2f}x")

print("\nRecommendations:")
print("- Use Method 3 (Direct Access) for highest performance when data can be")
print("  processed immediately without long-term storage")
print("- Use Method 1 (Raw NumPy) for balance of speed and ease of use")
print("- Use Method 2 (Voltage NumPy) when you need data in voltage units")
print("=" * 70)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing resources...")
rp.rp_AcqAxiEnable(rp.RP_CH_1, False)
rp.rp_Release()
print("Resources released")
