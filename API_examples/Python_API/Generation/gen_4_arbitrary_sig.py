#!/usr/bin/python3
"""
Red Pitaya Arbitrary Waveform Generation Example
=================================================

This example demonstrates arbitrary waveform generation on Red Pitaya using
custom-defined waveforms. Instead of using predefined waveforms (sine, square,
etc.), arbitrary waveforms allow you to create any signal shape by defining
sample values. This example creates two different custom waveforms and outputs
them synchronously on both channels.

Features:
- Custom arbitrary waveform generation
- Dual-channel synchronized output
- User-defined waveform data using NumPy
- Configurable frequency and amplitude
- Output synchronization between channels

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup:
  Connect oscilloscope or measurement device to OUT1 and OUT2
  to observe the synchronized custom waveforms

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- OS 2.00 or higher

Usage:
    python gen_4_arbitrary_sig.py
    
    The program will generate two different arbitrary waveforms:
    - OUT1: sin(t) + (1/3)*sin(3t) - a sine wave with 3rd harmonic
    - OUT2: (1/2)*sin(t) + (1/4)*sin(4t) - a sine wave with 4th harmonic

Configuration:
    Modify parameters in the CONFIGURATION section:
    - channel, channel2: Output channels
    - freq: Signal frequency in Hz
    - ampl: Signal amplitude in volts
    - N: Number of samples in waveform buffer (max 16384)

    Modify waveform generation in CUSTOM WAVEFORM SETUP section
    to create different arbitrary waveforms.

Author: Red Pitaya
Date: January 2026
"""

import time
import numpy as np
import rp


# ==============================================================================
# CONFIGURATION - Set your arbitrary waveform generation parameters
# ==============================================================================

# Generator output channels
# Available channels:
#   RP_CH_1 - Output channel 1 (OUT1)
#   RP_CH_2 - Output channel 2 (OUT2)

channel = rp.RP_CH_1
channel2 = rp.RP_CH_2

# Waveform type (must be ARBITRARY for custom waveforms)
waveform = rp.RP_WAVEFORM_ARBITRARY

# Signal parameters
freq = 10000                    # Frequency in Hz (10 kHz)
ampl = 1                        # Amplitude in volts (peak amplitude)

# Arbitrary waveform buffer size
N = 16384                       # Number of samples in the buffer (max 16384)

print("=" * 70)
print("Red Pitaya Arbitrary Waveform Generation Configuration")
print("=" * 70)
print(f"Output channels:     OUT1 and OUT2 (synchronized)")
print(f"Waveform type:       ARBITRARY (custom)")
print(f"Frequency:           {freq} Hz")
print(f"Amplitude:           {ampl} V (peak)")
print(f"Buffer size:         {N} samples")
print()
print("Custom Waveforms:")
print("  OUT1: sin(t) + (1/3)*sin(3t)")
print("  OUT2: (1/2)*sin(t) + (1/4)*sin(4t)")
print("=" * 70)


# ==============================================================================
# CUSTOM WAVEFORM SETUP - Create arbitrary waveform data
# ==============================================================================

print("\nCreating custom arbitrary waveforms...")

# Allocate buffers for arbitrary waveforms
x = rp.arbBuffer(N)
y = rp.arbBuffer(N)

# Create time vector (0 to 2π)
t = np.linspace(0, 1, N) * 2 * np.pi

# Define custom waveforms using NumPy
# Channel 1: Fundamental + 3rd harmonic
x_temp = np.sin(t) + 1/3 * np.sin(3*t)

# Channel 2: Fundamental with different harmonics
y_temp = 1/2 * np.sin(t) + 1/4 * np.sin(4*t)

# Normalize waveforms to fit within [-1, 1] range
x_max = np.max(np.abs(x_temp))
y_max = np.max(np.abs(y_temp))
x_temp = x_temp / x_max
y_temp = y_temp / y_max

# Copy data to Red Pitaya buffers
for i in range(0, N, 1):
    x[i] = float(x_temp[i])
    y[i] = float(y_temp[i])

print(f"Arbitrary waveform buffers created ({N} samples each)")
print(f"  OUT1 waveform normalized by factor: {x_max:.3f}")
print(f"  OUT2 waveform normalized by factor: {y_max:.3f}")


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya
# ==============================================================================

print("\nInitializing Red Pitaya...")

# Initialize the Red Pitaya interface
rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# RESET - Reset generator to default state
# ==============================================================================

print("\nResetting generator...")

# Reset generation to default state
rp.rp_GenReset()
print("Generator reset to default state")


# ==============================================================================
# SIGNAL GENERATION SETUP - Configure arbitrary waveforms
# ==============================================================================

print("\nConfiguring arbitrary waveform generation...")

# Configure Channel 1 (OUT1)
print("\nConfiguring OUT1...")
rp.rp_GenWaveform(channel, waveform)
print(f"  Waveform type set: ARBITRARY")

rp.rp_GenArbWaveform(channel, x.cast(), N)
print(f"  Arbitrary waveform loaded ({N} samples)")

rp.rp_GenFreqDirect(channel, freq)
print(f"  Frequency set: {freq} Hz")

rp.rp_GenAmp(channel, ampl)
print(f"  Amplitude set: {ampl} V")


# Configure Channel 2 (OUT2)
print("\nConfiguring OUT2...")
rp.rp_GenWaveform(channel2, waveform)
print(f"  Waveform type set: ARBITRARY")

rp.rp_GenArbWaveform(channel2, y.cast(), N)
print(f"  Arbitrary waveform loaded ({N} samples)")

rp.rp_GenFreqDirect(channel2, freq)
print(f"  Frequency set: {freq} Hz")

rp.rp_GenAmp(channel2, ampl)
print(f"  Amplitude set: {ampl} V")


# ==============================================================================
# TRIGGER CONFIGURATION - Set trigger source
# ==============================================================================

print("\nConfiguring trigger source...")

# Available trigger sources:
#   RP_GEN_TRIG_SRC_INTERNAL - Internal trigger (immediate)
#   RP_GEN_TRIG_SRC_EXT_PE   - External trigger positive edge
#   RP_GEN_TRIG_SRC_EXT_NE   - External trigger negative edge

# Specify generator trigger source
rp.rp_GenTriggerSource(channel, rp.RP_GEN_TRIG_SRC_INTERNAL)
print("Trigger source set: INTERNAL")


# ==============================================================================
# OUTPUT SYNCHRONIZATION - Synchronize and enable outputs
# ==============================================================================

print("\nEnabling synchronized output...")

# Enable output synchronization
rp.rp_GenOutEnableSync(True)
print("Output synchronization enabled")

# Enable output channel 1
rp.rp_GenOutEnable(channel)
print("OUT1 enabled")

# Synchronize output channels
rp.rp_GenSynchronise()
print("Output channels synchronized")

# Trigger generator to start synchronized output
rp.rp_GenTriggerOnly(channel)
print("Generator triggered - synchronized arbitrary waveforms started")

print("\n" + "=" * 70)
print("Synchronized arbitrary waveform generation active!")
print("OUT1: sin(t) + (1/3)*sin(3t)")
print("OUT2: (1/2)*sin(t) + (1/4)*sin(4t)")
print("Both channels synchronized at the same frequency")
print("Connect oscilloscope to OUT1 and OUT2 to observe the waveforms")
print("=" * 70)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing Red Pitaya resources...")

# Release resources and stop generation
rp.rp_Release()
print("Resources released - arbitrary waveform generation stopped")
print("\nProgram completed successfully")
