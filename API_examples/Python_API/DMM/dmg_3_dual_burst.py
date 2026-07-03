#!/usr/bin/python3
"""
Red Pitaya DMG (Direct Memory Generation) Dual-Channel Burst Mode Example
==========================================================================

This example demonstrates synchronized dual-channel burst mode waveform generation
using DMG (Direct Memory Generation) on Red Pitaya. Burst mode allows generating a
specified number of waveform cycles with controlled repetition rate on both output
channels simultaneously.

Features:
- Dual-channel synchronized burst mode generation (OUT1 and OUT2)
- Configurable number of cycles per burst
- Configurable burst repetition count and period
- Independent amplitude control per channel
- Direct memory access for high-speed operation
- Custom arbitrary waveforms with different shapes per channel
- Synchronized trigger for phase-locked outputs

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Optional: Oscilloscope to view synchronized burst outputs

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- rp_overlay module

Usage:
    python dmg_3_dual_burst.py

Configuration:
    Modify the parameters in the CONFIGURATION section below:
    - cycles: Number of sine cycles in the waveform
    - resolution: Number of samples per waveform
    - amplitude_ch1, amplitude_ch2: Output amplitudes per channel
    - cycles_per_burst: Number of waveform cycles in each burst
    - burst_repetitions: Number of times to repeat the burst
    - burst_period: Time between burst starts (microseconds)
    - decimation_factor: Output rate decimation

Note:
    This example generates different waveforms on each channel:
    - Channel 1: Rectified sine wave (abs(sin))
    - Channel 2: Modified sine with offset and clamping
    
    Both channels are synchronized and triggered together for phase-locked burst output.

Author: Red Pitaya
Date: January 2026
"""

import numpy as np
from rp_overlay import overlay
import rp
import math


# ==============================================================================
# CONFIGURATION - Set your generation parameters here
# ==============================================================================

# Waveform parameters
cycles = 1                      # Number of sine cycles in the waveform
resolution = 128 * 1024         # Number of samples (128K samples)

# Amplitude settings per channel
amplitude_ch1 = 1.0             # OUT1 amplitude in volts
amplitude_ch2 = 0.8             # OUT2 amplitude in volts

# Burst mode parameters
cycles_per_burst = 1            # Number of waveform cycles in each burst
burst_repetitions = 3           # Number of times to repeat the burst
burst_period = 2000             # Time between burst starts in microseconds (2 ms)

# Generator settings
decimation_factor = 1           # Decimation factor (1 = 125 MS/s)

print("=" * 70)
print("Red Pitaya DMG Dual-Channel Burst Mode Configuration")
print("=" * 70)
print(f"Waveform cycles:     {cycles}")
print(f"Resolution:          {resolution:,} samples")
print(f"Amplitude CH1:       {amplitude_ch1} V")
print(f"Amplitude CH2:       {amplitude_ch2} V")
print(f"Decimation factor:   {decimation_factor} (Output rate: {125/decimation_factor:.2f} MS/s)")
print(f"Cycles per burst:    {cycles_per_burst}")
print(f"Burst repetitions:   {burst_repetitions}")
print(f"Burst period:        {burst_period} μs ({burst_period/1000:.1f} ms)")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya and FPGA
# ==============================================================================

print("\nInitializing Red Pitaya...")

# Load FPGA overlay (v0.94 or compatible)
fpga = overlay()
print("FPGA overlay loaded")

# Optional: Enable debug register for troubleshooting
# rp.rp_EnableDebugReg()

# Initialize Red Pitaya API
rp.rp_Init()

# Reset generator configuration
rp.rp_GenReset()
print("Red Pitaya initialized and generator reset")


# ==============================================================================
# DMG MEMORY SETUP - Configure DMG memory regions
# ==============================================================================

print("\nConfiguring DMG memory regions...")

# Get available memory region for DMG
memory = rp.rp_AcqAxiGetMemoryRegion()
if memory[0] != rp.RP_OK:
    print("ERROR: Failed to access reserved memory")
    print("Make sure the Red Pitaya FPGA is properly configured")
    exit(1)

dmg_start_address = memory[1]
dmg_total_size = memory[2]

print(f"DMG Memory - Start: 0x{dmg_start_address:X}, Size: {dmg_total_size:,} bytes ({dmg_total_size / (1024**2):.2f} MB)")

# Calculate buffer size in bytes (int16 = 2 bytes per sample)
buffer_size_bytes = resolution * 2

# Memory alignment constraint (4096 bytes spacing between channels)
min_address_alignment = 4096

# Calculate start addresses for both channels
channel1_start_address = dmg_start_address
channel1_end_address = channel1_start_address + buffer_size_bytes

channel2_start_address = channel1_start_address + buffer_size_bytes + min_address_alignment
channel2_end_address = channel2_start_address + buffer_size_bytes

print(f"OUT1 Buffer - Start: 0x{channel1_start_address:X}, Size: {buffer_size_bytes:,} bytes, "
      f"End: 0x{channel1_end_address:X}")
print(f"OUT2 Buffer - Start: 0x{channel2_start_address:X}, Size: {buffer_size_bytes:,} bytes, "
      f"End: 0x{channel2_end_address:X}")

# Reserve memory regions for both generator channels
result = rp.rp_GenAxiReserveMemory(rp.RP_CH_1, channel1_start_address, channel1_end_address)
if result != rp.RP_OK:
    print("ERROR: Failed to reserve memory for OUT1")
    exit(1)

result = rp.rp_GenAxiReserveMemory(rp.RP_CH_2, channel2_start_address, channel2_end_address)
if result != rp.RP_OK:
    print("ERROR: Failed to reserve memory for OUT2")
    exit(1)

print("Memory regions reserved successfully")


# ==============================================================================
# AMPLITUDES CONFIGURATION - Set output amplitudes
# ==============================================================================

print("\nConfiguring output amplitudes...")

# Set amplitude for Channel 1
rp.rp_GenAmp(rp.RP_CH_1, amplitude_ch1)
print(f"OUT1 amplitude set to {amplitude_ch1} V")

# Set amplitude for Channel 2
rp.rp_GenAmp(rp.RP_CH_2, amplitude_ch2)
print(f"OUT2 amplitude set to {amplitude_ch2} V")


# ==============================================================================
# BURST MODE CONFIGURATION - Set burst parameters
# ==============================================================================

print("\nConfiguring burst mode parameters...")

# Configure burst mode for Channel 1
rp.rp_GenMode(rp.RP_CH_1, rp.RP_GEN_MODE_BURST)
rp.rp_GenBurstCount(rp.RP_CH_1, cycles_per_burst)
rp.rp_GenBurstRepetitions(rp.RP_CH_1, burst_repetitions)
rp.rp_GenBurstPeriod(rp.RP_CH_1, burst_period)
print(f"OUT1 burst mode: {cycles_per_burst} cycles × {burst_repetitions} reps, {burst_period} μs period")

# Configure burst mode for Channel 2
rp.rp_GenMode(rp.RP_CH_2, rp.RP_GEN_MODE_BURST)
rp.rp_GenBurstCount(rp.RP_CH_2, cycles_per_burst)
rp.rp_GenBurstRepetitions(rp.RP_CH_2, burst_repetitions)
rp.rp_GenBurstPeriod(rp.RP_CH_2, burst_period)
print(f"OUT2 burst mode: {cycles_per_burst} cycles × {burst_repetitions} reps, {burst_period} μs period")


# ==============================================================================
# WAVEFORM GENERATION - Create and load custom waveforms
# ==============================================================================

print("\nGenerating custom waveforms...")

# Create time array for waveform generation
length = np.pi * 2 * cycles
wave_ch1 = np.sin(np.arange(0, length, length / resolution, dtype=np.float32))
wave_ch2 = np.arange(0, length, length / resolution, dtype=np.float32)

# Channel 1: Rectified sine wave (absolute value)
for i in range(0, resolution):
    wave_ch1[i] = math.fabs(wave_ch1[i])

# Channel 2: Modified sine with offset and clamping
# Formula: |sin(t) + 0.5| clamped to [-1, 1]
for i in range(0, resolution):
    t = (2 * math.pi) / resolution * i
    b = math.fabs(math.sin(t) + 0.5)
    if b >= 1:
        b = 1
    if b <= -1:
        b = -1.0
    wave_ch2[i] = b

print("OUT1 Waveform: Rectified sine |sin(t)|")
print(f"  Samples: {resolution:,}, Range: [{wave_ch1.min():.3f}, {wave_ch1.max():.3f}]")
print("OUT2 Waveform: Modified sine |sin(t) + 0.5| clamped")
print(f"  Samples: {resolution:,}, Range: [{wave_ch2.min():.3f}, {wave_ch2.max():.3f}]")

# Write waveform data to both channels
rp.rp_GenAxiWriteWaveform(rp.RP_CH_1, wave_ch1)
rp.rp_GenAxiWriteWaveform(rp.RP_CH_2, wave_ch2)
print("Waveforms loaded to both output channels")


# ==============================================================================
# GENERATOR CONFIGURATION - Set up DMG parameters
# ==============================================================================

print("\nConfiguring generator parameters...")

# Set decimation factor for both channels
rp.rp_GenAxiSetDecimationFactor(rp.RP_CH_1, decimation_factor)
rp.rp_GenAxiSetDecimationFactor(rp.RP_CH_2, decimation_factor)
print(f"Decimation factor set to {decimation_factor} for both channels")

# Enable DMG (AXI) mode for both channels
rp.rp_GenAxiSetEnable(rp.RP_CH_1, True)
rp.rp_GenAxiSetEnable(rp.RP_CH_2, True)
print("DMG mode enabled for both channels")

# Set trigger source to internal
rp.rp_GenTriggerSource(rp.RP_CH_1, rp.RP_GEN_TRIG_SRC_INTERNAL)
print("Trigger source set to internal")


# ==============================================================================
# START GENERATION - Enable synchronized burst output
# ==============================================================================

print("\nStarting synchronized dual-channel burst generation...")

# Enable output synchronization between channels
rp.rp_GenOutEnableSync(True)
print("Output synchronization enabled")

# Synchronize and trigger both generators simultaneously
rp.rp_GenSynchronise()
print("Burst generation triggered")

print("\n" + "=" * 70)
print("DUAL-CHANNEL BURST GENERATION COMPLETE")
print("=" * 70)
print(f"Generated {burst_repetitions} synchronized burst(s) on OUT1 and OUT2")
print(f"Each burst contains {cycles_per_burst} cycle(s) of the waveform")
print(f"Burst period: {burst_period} μs ({burst_period/1000:.1f} ms)")
print(f"Total burst duration: ~{burst_period * burst_repetitions / 1000:.1f} ms")
print("\nWaveform details:")
print(f"  OUT1 (Amplitude: {amplitude_ch1} V): Rectified sine |sin(t)|")
print(f"  OUT2 (Amplitude: {amplitude_ch2} V): Modified sine |sin(t) + 0.5|")
print("\nConnect an oscilloscope to view the synchronized burst waveforms.")
print("The generators will output the configured bursts and then stop.")
print("=" * 70)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing resources...")

# Release memory reservations
rp.rp_GenAxiReleaseMemory(rp.RP_CH_1)
rp.rp_GenAxiReleaseMemory(rp.RP_CH_2)
print("Memory regions released")

# Release Red Pitaya resources
rp.rp_Release()
print("Resources released - burst generation complete")
