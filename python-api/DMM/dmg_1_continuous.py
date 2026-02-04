#!/usr/bin/python3
"""
Red Pitaya DMG (Direct Memory Generation) Continuous Output Example
====================================================================

This example demonstrates continuous waveform generation using DMG (Direct Memory
Generation) mode on Red Pitaya. DMG allows streaming arbitrary waveforms directly
from DDR memory to the DAC outputs for high-speed, continuous signal generation.

Features:
- Dual-channel simultaneous waveform generation (OUT1 and OUT2)
- Direct memory access for high-speed operation
- Configurable waveform size and decimation
- Synchronized output between channels
- Custom arbitrary waveform generation (sine + 3rd harmonic)

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Optional: Oscilloscope to view outputs on OUT1 and OUT2

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- rp_overlay module

Usage:
    python dmg_continuous.py

Configuration:
    Modify the parameters in the CONFIGURATION section below:
    - buffer_size: Number of samples in the waveform buffer
    - decimation_factor: Output rate decimation (1 = 125 MS/s)
    - num_buffers: Number of buffers to use (1 or 2)

Note:
    Buffer start addresses must be aligned to DDR page size (4096 bytes).
    The example generates a composite waveform (fundamental + 3rd harmonic).

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

# Generation parameters
buffer_size = 64                # Number of samples in waveform buffer per channel
decimation_factor = 1           # Decimation factor (1 = 125 MS/s, 2 = 62.5 MS/s, etc.)
num_buffers = 2                 # Number of buffers to use (1 or 2)

# Memory alignment constraint (DDR page size - do not modify)
min_address_alignment = 4096    # Minimum spacing between buffer start addresses (bytes)

print("=" * 70)
print("Red Pitaya DMG Continuous Generation Configuration")
print("=" * 70)
print(f"Buffer size:         {buffer_size} samples")
print(f"Decimation factor:   {decimation_factor} (Output rate: {125/decimation_factor:.2f} MS/s)")
print(f"Number of buffers:   {num_buffers}")
print(f"Memory alignment:    {min_address_alignment} bytes")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya and FPGA
# ==============================================================================

print("\nInitializing Red Pitaya...")

# Load FPGA overlay (v0.94 or compatible)
fpga = overlay()

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

print(f"DMG Memory - Start: 0x{dmg_start_address:X}, Size: {dmg_total_size:,} bytes ({dmg_total_size / 1024:.1f} KB)")

# Calculate buffer size in bytes (int16 = 2 bytes per sample)
buffer_size_bytes = buffer_size * 2

# Calculate aligned single buffer size (must be multiple of min_address_alignment)
dmg_single_buffer_size = max(buffer_size_bytes, min_address_alignment)
dmg_single_buffer_size = int(math.ceil(dmg_single_buffer_size / min_address_alignment) * min_address_alignment)
dmg_minimum_required_size = dmg_single_buffer_size * num_buffers

# Check if requested size fits in available memory
if dmg_minimum_required_size > dmg_total_size:
    print(f"WARNING: Requested buffer size ({dmg_minimum_required_size} bytes) exceeds available memory")
    print("Reducing buffer size to fit available memory...")
    
    buffer_size = int(dmg_total_size / (4 * num_buffers))
    buffer_size_bytes = buffer_size * 2
    dmg_single_buffer_size = max(buffer_size_bytes, min_address_alignment)
    dmg_single_buffer_size = int(math.ceil(dmg_single_buffer_size / min_address_alignment) * min_address_alignment)
    
    print(f"Adjusted buffer size: {buffer_size} samples")

# Calculate start addresses for both channels
channel1_start_address = dmg_start_address
channel2_start_address = dmg_start_address + dmg_single_buffer_size

print(f"OUT1 Buffer - Start: 0x{channel1_start_address:X}, Size: {buffer_size_bytes} bytes, "
      f"End: 0x{channel1_start_address + buffer_size_bytes:X}")
print(f"OUT2 Buffer - Start: 0x{channel2_start_address:X}, Size: {buffer_size_bytes} bytes, "
      f"End: 0x{channel2_start_address + buffer_size_bytes:X}")

# Reserve memory regions for both generator channels
result = rp.rp_GenAxiReserveMemory(rp.RP_CH_1, channel1_start_address, 
                                    channel1_start_address + buffer_size_bytes)
if result != rp.RP_OK:
    print("ERROR: Failed to reserve memory for OUT1")
    exit(1)

result = rp.rp_GenAxiReserveMemory(rp.RP_CH_2, channel2_start_address, 
                                    channel2_start_address + buffer_size_bytes)
if result != rp.RP_OK:
    print("ERROR: Failed to reserve memory for OUT2")
    exit(1)

print("Memory regions reserved successfully")


# ==============================================================================
# WAVEFORM GENERATION - Create and load waveform data
# ==============================================================================

print("\nGenerating waveform data...")

# Create time array for one period
t = np.linspace(0, 2*np.pi, buffer_size, endpoint=False, dtype=np.float32)

# Generate composite waveform: fundamental sine + 3rd harmonic
# This creates a more complex waveform than a pure sine wave
waveform_data = np.sin(t) + (1/3) * np.sin(3*t)

print(f"Waveform: sin(t) + (1/3)*sin(3t)")
print(f"Samples: {buffer_size}, Range: [{waveform_data.min():.3f}, {waveform_data.max():.3f}]")

# Write waveform data to both channels
rp.rp_GenAxiWriteWaveform(rp.RP_CH_1, waveform_data)
rp.rp_GenAxiWriteWaveform(rp.RP_CH_2, waveform_data)
print("Waveform loaded to both output channels")


# ==============================================================================
# GENERATOR CONFIGURATION - Set up output parameters
# ==============================================================================

print("\nConfiguring generator parameters...")

# Set decimation factor for both channels
result = rp.rp_GenAxiSetDecimationFactor(rp.RP_CH_1, decimation_factor)
if result != rp.RP_OK:
    print("ERROR: Failed to set decimation for OUT1")
    exit(1)

result = rp.rp_GenAxiSetDecimationFactor(rp.RP_CH_2, decimation_factor)
if result != rp.RP_OK:
    print("ERROR: Failed to set decimation for OUT2")
    exit(1)

print(f"Decimation factor set to {decimation_factor} for both channels")

# Enable DMG (AXI) mode for both channels
result = rp.rp_GenAxiSetEnable(rp.RP_CH_1, True)
if result != rp.RP_OK:
    print("ERROR: Failed to enable DMG mode for OUT1")
    exit(1)

result = rp.rp_GenAxiSetEnable(rp.RP_CH_2, True)
if result != rp.RP_OK:
    print("ERROR: Failed to enable DMG mode for OUT2")
    exit(1)

print("DMG mode enabled for both channels")

# Configure amplitude and offset calibration
rp.rp_GenSetAmplitudeAndOffsetOrigin(rp.RP_CH_1)
rp.rp_GenSetAmplitudeAndOffsetOrigin(rp.RP_CH_2)

# Set trigger source to internal (free-running)
rp.rp_GenTriggerSource(rp.RP_CH_1, rp.RP_GEN_TRIG_SRC_INTERNAL)


# ==============================================================================
# START GENERATION - Enable synchronized output
# ==============================================================================

print("\nStarting synchronized generation...")

# Enable output synchronization between channels
rp.rp_GenOutEnableSync(True)

# Synchronize and start both generators simultaneously
rp.rp_GenSynchronise()

print("Generation started on OUT1 and OUT2")
print("\n" + "=" * 70)
print("CONTINUOUS GENERATION ACTIVE")
print("=" * 70)
print("The waveform is now being continuously output on both channels.")
print("Connect an oscilloscope to OUT1 and OUT2 to view the signals.")
print("Press Ctrl+C to stop generation and exit.")
print("=" * 70)

try:
    # Keep the program running to maintain continuous generation
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nStopping generation...")


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing resources...")

# Release memory reservations
rp.rp_GenAxiReleaseMemory(rp.RP_CH_1)
rp.rp_GenAxiReleaseMemory(rp.RP_CH_2)

# Release Red Pitaya resources
rp.rp_Release()

print("Resources released - generation stopped")
