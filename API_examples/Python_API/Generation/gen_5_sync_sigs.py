#!/usr/bin/python3
"""
Red Pitaya Synchronized Signal Generation Example
==================================================

This example demonstrates synchronized signal generation on both output channels
of Red Pitaya. Both channels are configured with identical parameters and then
synchronized to start at exactly the same time. This ensures phase alignment
between the two outputs, which is essential for applications requiring
phase-coherent signals, such as IQ modulation, differential signals, or
multi-channel testing.

Features:
- Dual-channel synchronized output
- Phase-aligned signal generation
- Configurable waveform type, frequency, and amplitude
- Internal trigger for simultaneous start
- Precise timing control

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup:
  Connect oscilloscope or measurement device to OUT1 and OUT2
  to observe the synchronized signals with zero phase difference

Software Requirements:
- Red Pitaya Python API (rp module)
- OS 2.00 or higher

Usage:
    python gen_5_sync_sigs.py
    
    The program will generate synchronized signals on both OUT1 and OUT2.
    When measured on an oscilloscope, both signals should be perfectly
    phase-aligned (zero phase difference at startup).

Configuration:
    Modify parameters in the CONFIGURATION section:
    - channel, channel2: Output channels (always CH_1 and CH_2)
    - waveform: Waveform type (SINE, SQUARE, etc.)
    - freq: Signal frequency in Hz
    - ampl: Signal amplitude in volts
    - gen_trig_sour: Trigger source for synchronization

Author: Red Pitaya
Date: January 2026
"""

import time
import numpy as np
import rp


# ==============================================================================
# CONFIGURATION - Set your synchronized signal generation parameters
# ==============================================================================

# Generator output channels
# Available channels:
#   RP_CH_1 - Output channel 1 (OUT1)
#   RP_CH_2 - Output channel 2 (OUT2)

channel = rp.RP_CH_1
channel2 = rp.RP_CH_2

# Waveform type (same for both channels)
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

# Signal parameters (same for both channels)
freq = 10000                    # Frequency in Hz (10 kHz)
ampl = 1                        # Amplitude in volts (peak amplitude)

# Generator trigger source
# Available trigger sources:
#   RP_GEN_TRIG_SRC_INTERNAL - Internal trigger (immediate)
#   RP_GEN_TRIG_SRC_EXT_PE   - External trigger positive edge
#   RP_GEN_TRIG_SRC_EXT_NE   - External trigger negative edge

gen_trig_sour = rp.RP_GEN_TRIG_SRC_INTERNAL

print("=" * 70)
print("Red Pitaya Synchronized Signal Generation Configuration")
print("=" * 70)
print(f"Output channels:     OUT1 and OUT2 (synchronized)")
print(f"Waveform:            {waveform}")
print(f"Frequency:           {freq} Hz")
print(f"Amplitude:           {ampl} V (peak)")
print(f"Trigger source:      INTERNAL")
print()
print("Note: Both channels configured with identical parameters")
print("      for phase-aligned synchronous output")
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
# SIGNAL GENERATION SETUP - Configure both output channels
# ==============================================================================

print("\nConfiguring signal generation...")

# Configure Channel 1 (OUT1)
print("\nConfiguring OUT1...")
rp.rp_GenWaveform(channel, waveform)
print(f"  Waveform type set: {waveform}")

rp.rp_GenFreqDirect(channel, freq)
print(f"  Frequency set: {freq} Hz")

rp.rp_GenAmp(channel, ampl)
print(f"  Amplitude set: {ampl} V")


# Configure Channel 2 (OUT2)
print("\nConfiguring OUT2...")
rp.rp_GenWaveform(channel2, waveform)
print(f"  Waveform type set: {waveform}")

rp.rp_GenFreqDirect(channel2, freq)
print(f"  Frequency set: {freq} Hz")

rp.rp_GenAmp(channel2, ampl)
print(f"  Amplitude set: {ampl} V")


# ==============================================================================
# TRIGGER CONFIGURATION - Set trigger source
# ==============================================================================

print("\nConfiguring trigger source...")

# Specify generator trigger source
rp.rp_GenTriggerSource(channel, gen_trig_sour)
print("Trigger source set: INTERNAL")


# ==============================================================================
# OUTPUT SYNCHRONIZATION - Synchronize and enable outputs
# ==============================================================================

print("\nEnabling synchronized output...")

# Enable output synchronization
# This ensures both channels start at exactly the same time
rp.rp_GenOutEnableSync(True)
print("Output synchronization enabled")

# Enable output channel 1
# (Channel 2 will be automatically synchronized)
rp.rp_GenOutEnable(channel)
print("OUT1 enabled")

# Synchronize output channels
# This prepares both channels for simultaneous start
rp.rp_GenSynchronise()
print("Output channels synchronized")

# Trigger generator to start synchronized output
# Both channels will start at exactly the same time
rp.rp_GenTriggerOnly(channel)
print("Generator triggered - synchronized signal output started")

print("\n" + "=" * 70)
print("Synchronized signal generation active!")
print("Both OUT1 and OUT2 are generating phase-aligned signals")
print("Connect oscilloscope to both channels to verify synchronization")
print("Expected: Zero phase difference between channels")
print("=" * 70)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing Red Pitaya resources...")

# Release resources and stop generation
rp.rp_Release()
print("Resources released - synchronized generation stopped")
print("\nProgram completed successfully")
