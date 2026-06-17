#!/usr/bin/python3
"""
Red Pitaya DMG (Direct Memory Generation) Burst Mode Example
=============================================================

This example demonstrates burst mode waveform generation using DMG (Direct Memory
Generation) on Red Pitaya. Burst mode allows generating a specified number of
waveform cycles with controlled repetition rate, useful for pulsed applications.

Features:
- Single-channel burst mode generation
- Configurable number of cycles per burst
- Configurable burst repetition count
- Adjustable burst period (repetition rate)
- Direct memory access for high-speed operation
- Custom arbitrary waveform (sine + 3rd harmonic)

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Optional: Oscilloscope to view burst output

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- rp_overlay module

Usage:
    python dmg_burst.py

Configuration:
    Modify the parameters in the CONFIGURATION section below:
    - output_channel: Select output channel (RP_CH_1 or RP_CH_2)
    - buffer_size: Number of samples in waveform buffer
    - decimation_factor: Output rate decimation
    - cycles_per_burst: Number of waveform cycles in each burst
    - burst_repetitions: Number of times to repeat the burst
    - burst_period: Time between burst starts (microseconds)

Note:
    Burst mode generates a finite number of waveform cycles, waits for the
    specified period, then repeats. Useful for radar, ultrasound, and pulsed
    measurement applications.

Author: Red Pitaya
"""

import time
import math
import numpy as np
from rp_overlay import overlay
import rp


# ==============================================================================
# CONFIGURATION - Set your generation parameters here
# ==============================================================================

# Channel selection
output_channel = rp.RP_CH_1     # Output channel (RP_CH_1 for OUT1, RP_CH_2 for OUT2)

# Waveform buffer parameters
buffer_size = 4096              # Buffer size in bytes (will be divided by 2 for samples)
decimation_factor = 1           # Decimation factor (1 = 125 MS/s, 2 = 62.5 MS/s, etc.)

# Burst mode parameters
cycles_per_burst = 2            # Number of waveform cycles in each burst
burst_repetitions = 2           # Number of times to repeat the burst
burst_period = 100              # Time between burst starts in microseconds

channel_name = "OUT1" if output_channel == rp.RP_CH_1 else "OUT2"

print("=" * 70)
print("Red Pitaya DMG Burst Mode Configuration")
print("=" * 70)
print(f"Output channel:      {channel_name}")
print(f"Buffer size:         {buffer_size} bytes")
print(f"Decimation factor:   {decimation_factor} (Output rate: {125/decimation_factor:.2f} MS/s)")
print(f"Cycles per burst:    {cycles_per_burst}")
print(f"Burst repetitions:   {burst_repetitions}")
print(f"Burst period:        {burst_period} μs")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya and FPGA
# ==============================================================================

print("\nInitializing Red Pitaya...")

# Load FPGA overlay (v0.94 or compatible)
fpga = overlay()

# Initialize Red Pitaya API
rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# DMG MEMORY SETUP - Configure DMG memory region
# ==============================================================================

print("\nConfiguring DMG memory...")

# Get available memory region for DMG
memory = rp.rp_AcqAxiGetMemoryRegion()
if memory[0] != rp.RP_OK:
    print("ERROR: Failed to get reserved memory")
    print("Make sure the Red Pitaya FPGA is properly configured")
    exit(1)

dmg_start_address = memory[1]
dmg_total_size = memory[2]

print(f"DMG Memory - Start: 0x{dmg_start_address:X}, Size: {dmg_total_size:,} bytes ({dmg_total_size / 1024:.1f} KB)")

# Adjust buffer size if it exceeds available memory
if dmg_total_size < buffer_size:
    print(f"WARNING: Requested buffer size ({buffer_size} bytes) exceeds available memory")
    buffer_size = dmg_total_size
    print(f"Adjusted buffer size to {buffer_size} bytes")

# Reserve memory for the generator
result = rp.rp_GenAxiReserveMemory(output_channel, dmg_start_address, 
                                    dmg_start_address + buffer_size)
if result != rp.RP_OK:
    print(f"ERROR: Failed to reserve memory for {channel_name}")
    exit(1)

print(f"{channel_name} Buffer - Start: 0x{dmg_start_address:X}, Size: {buffer_size} bytes, "
      f"End: 0x{dmg_start_address + buffer_size:X}")
print("Memory region reserved successfully")


# ==============================================================================
# GENERATOR CONFIGURATION - Set up DMG parameters
# ==============================================================================

print("\nConfiguring generator parameters...")

# Set decimation factor
result = rp.rp_GenAxiSetDecimationFactor(output_channel, decimation_factor)
if result != rp.RP_OK:
    print(f"ERROR: Failed to set decimation for {channel_name}")
    exit(1)

print(f"Decimation factor set to {decimation_factor}")

# Enable DMG (AXI) mode
result = rp.rp_GenAxiSetEnable(output_channel, True)
if result != rp.RP_OK:
    print(f"ERROR: Failed to enable DMG mode for {channel_name}")
    exit(1)

print(f"DMG mode enabled for {channel_name}")


# ==============================================================================
# WAVEFORM GENERATION - Create and load waveform data
# ==============================================================================

print("\nGenerating waveform data...")

# Calculate number of samples (buffer_size is in bytes, int16 = 2 bytes per sample)
num_samples = int(buffer_size / 2)

# Create time array for one period
t = np.linspace(0, 2*np.pi, num_samples, endpoint=False, dtype=np.float32)

# Generate composite waveform: fundamental sine + 3rd harmonic
waveform_data = np.sin(t) + (1/3) * np.sin(3*t)

print(f"Waveform: sin(t) + (1/3)*sin(3t)")
print(f"Samples: {num_samples}, Range: [{waveform_data.min():.3f}, {waveform_data.max():.3f}]")

# Configure amplitude and offset calibration
rp.rp_GenSetAmplitudeAndOffsetOrigin(output_channel)

# Configure burst mode parameters
rp.rp_GenMode(output_channel, rp.RP_GEN_MODE_BURST)
rp.rp_GenBurstCount(output_channel, int(cycles_per_burst))
rp.rp_GenBurstRepetitions(output_channel, int(burst_repetitions))
rp.rp_GenBurstPeriod(output_channel, int(burst_period))

print(f"Burst mode configured: {cycles_per_burst} cycles × {burst_repetitions} repetitions, "
      f"{burst_period} μs period")

# Write waveform data to channel
rp.rp_GenAxiWriteWaveform(output_channel, waveform_data)
print("Waveform loaded to output channel")


# ==============================================================================
# START GENERATION - Enable output and trigger burst
# ==============================================================================

print("\nStarting burst generation...")

# Enable output
rp.rp_GenOutEnable(output_channel)

# Trigger burst generation
rp.rp_GenTriggerOnly(output_channel)

print("\n" + "=" * 70)
print("BURST GENERATION TRIGGERED")
print("=" * 70)
print(f"Generated {burst_repetitions} burst(s) on {channel_name}")
print(f"Each burst contains {cycles_per_burst} cycle(s) of the waveform")
print(f"Burst period: {burst_period} μs")
print("\nConnect an oscilloscope to view the burst waveform.")
print("The generator will output the configured bursts and then stop.")
print("=" * 70)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing resources...")

# Release Red Pitaya resources
rp.rp_Release()

print("Resources released - burst generation complete")
