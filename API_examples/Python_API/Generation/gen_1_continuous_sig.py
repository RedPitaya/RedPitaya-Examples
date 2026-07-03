#!/usr/bin/python3
"""
Red Pitaya Continuous Signal Generation Example
================================================

This example demonstrates basic continuous signal generation on Red Pitaya.
It configures one of the output channels to generate a continuous waveform
with specified frequency and amplitude.

Features:
- Continuous waveform generation on output channels
- Configurable waveform type, frequency, and amplitude
- Simple setup for basic signal generation tasks
- Direct frequency setting for precise control

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup:
  Connect oscilloscope or measurement device to OUT1
  The generator will output a continuous signal that can be measured

Software Requirements:
- Red Pitaya Python API (rp module)
- OS 2.00 or higher

Usage:
    python gen_1_continuous_sig.py
    
    The program will generate a continuous signal on the selected output channel.
    The signal will continue until the program is stopped or resources are released.

Configuration:
    Modify parameters in the CONFIGURATION section:
    - channel: Output channel (RP_CH_1 or RP_CH_2)
    - waveform: Waveform type (SINE, SQUARE, TRIANGLE, etc.)
    - freq: Signal frequency in Hz
    - ampl: Signal amplitude in volts (peak amplitude)

Author: Red Pitaya
Date: January 2026
"""

import time
import rp


# ==============================================================================
# CONFIGURATION - Set your signal generation parameters
# ==============================================================================

# Generator output channel
# Available channels:
#   RP_CH_1 - Output channel 1 (OUT1)
#   RP_CH_2 - Output channel 2 (OUT2)

channel = rp.RP_CH_1

# Waveform type
# Available waveforms:
#   RP_WAVEFORM_SINE      - Sine wave
#   RP_WAVEFORM_SQUARE    - Square wave
#   RP_WAVEFORM_TRIANGLE  - Triangle wave
#   RP_WAVEFORM_RAMP_UP   - Ramp up (sawtooth ascending)
#   RP_WAVEFORM_RAMP_DOWN - Ramp down (sawtooth descending)
#   RP_WAVEFORM_DC        - DC signal (positive)
#   RP_WAVEFORM_PWM       - Pulse Width Modulation
#   RP_WAVEFORM_ARBITRARY - Arbitrary waveform (user-defined)
#   RP_WAVEFORM_DC_NEG    - DC signal (negative)
#   RP_WAVEFORM_SWEEP     - Frequency sweep

waveform = rp.RP_WAVEFORM_SINE

# Signal parameters
freq = 2000                     # Frequency in Hz (2 kHz)
ampl = 1                        # Amplitude in volts (peak amplitude)

print("=" * 70)
print("Red Pitaya Continuous Signal Generation Configuration")
print("=" * 70)
print(f"Output channel:      OUT{1 if channel == rp.RP_CH_1 else 2}")
print(f"Waveform:            {waveform}")
print(f"Frequency:           {freq} Hz")
print(f"Amplitude:           {ampl} V (peak)")
print("=" * 70)


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
# SIGNAL GENERATION SETUP - Configure output waveform
# ==============================================================================

print("\nConfiguring signal generation...")

# Set waveform type
rp.rp_GenWaveform(channel, waveform)
print(f"Waveform type set: {waveform}")

# Set frequency using direct method
rp.rp_GenFreqDirect(channel, freq)
print(f"Frequency set: {freq} Hz")

# Set amplitude
rp.rp_GenAmp(channel, ampl)
print(f"Amplitude set: {ampl} V")


# ==============================================================================
# OUTPUT ENABLE - Enable output and start generation
# ==============================================================================

print("\nEnabling output and starting generation...")

# Enable output channel
rp.rp_GenOutEnable(channel)
print(f"Output channel OUT{1 if channel == rp.RP_CH_1 else 2} enabled")

# Trigger the generator to start output
rp.rp_GenTriggerOnly(channel)
print("Generator triggered - continuous signal output started")

print("\n" + "=" * 70)
print("Signal generation active!")
print(f"Connect oscilloscope to OUT{1 if channel == rp.RP_CH_1 else 2} to observe the signal")
print("=" * 70)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing Red Pitaya resources...")

# Release resources and stop generation
rp.rp_Release()
print("Resources released - signal generation stopped")
print("\nProgram completed successfully")
