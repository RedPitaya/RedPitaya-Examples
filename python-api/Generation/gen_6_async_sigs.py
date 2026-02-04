#!/usr/bin/python3
"""
Red Pitaya Asynchronous Signal Generation Example
==================================================

This example demonstrates asynchronous (non-synchronized) burst signal generation
on both output channels of Red Pitaya. Unlike synchronized generation, the two
channels are triggered independently at different times, creating a deliberate
phase offset between them. This is useful for testing phase-sensitive systems,
simulating timing delays, or creating intentionally offset signals.

Features:
- Dual-channel asynchronous burst generation
- Independent triggering of each channel
- Configurable time delay between channel triggers
- Phase offset demonstration between channels
- Burst mode with configurable parameters

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup:
  Connect oscilloscope or measurement device to OUT1 and OUT2
  to observe the asynchronous signals with phase offset

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- Matplotlib library (imported but not used in this example)
- OS 2.00 or higher

Usage:
    python gen_6_async_sigs.py
    
    The program will generate burst signals on both channels, but
    trigger them at different times (0.5 second delay), creating
    a phase offset between OUT1 and OUT2.

Configuration:
    Modify parameters in the CONFIGURATION section:
    - channel, channel2: Output channels
    - waveform: Waveform type (SINE, SQUARE, etc.)
    - freq: Signal frequency in Hz
    - ampl: Signal amplitude in volts
    - ncyc: Number of cycles per burst
    - nor: Number of burst repetitions
    - period: Burst period in microseconds
    - trigger_delay: Time delay between channel triggers

Author: Red Pitaya
Date: January 2026
"""

import time
import numpy as np
from matplotlib import pyplot as plt
import rp


# ==============================================================================
# CONFIGURATION - Set your asynchronous signal generation parameters
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
freq = 10                       # Frequency in Hz (10 Hz - low for visualization)
ampl = 1                        # Amplitude in volts (peak amplitude)

# Burst mode parameters
ncyc = 2                        # Number of waveform periods per burst
nor = 1                         # Number of burst repetitions
period = 5000                   # Burst period in microseconds (5000 µs = 5 ms)

# Asynchronous trigger delay
trigger_delay = 0.5             # Time delay between channel triggers in seconds

# Calculate burst timing information
burst_duration_us = (ncyc / freq) * 1e6  # Duration of one burst in microseconds
phase_shift_deg = (trigger_delay * freq * 360) % 360  # Approximate phase shift

print("=" * 70)
print("Red Pitaya Asynchronous Signal Generation Configuration")
print("=" * 70)
print(f"Output channels:     OUT1 and OUT2 (asynchronous)")
print(f"Waveform:            {waveform}")
print(f"Frequency:           {freq} Hz")
print(f"Amplitude:           {ampl} V (peak)")
print()
print("Burst Mode Parameters:")
print(f"  Cycles per burst:  {ncyc}")
print(f"  Burst repetitions: {nor}")
print(f"  Burst period:      {period} µs ({period/1000:.2f} ms)")
print(f"  Burst duration:    {burst_duration_us:.2f} µs")
print()
print("Asynchronous Triggering:")
print(f"  OUT1 triggered first")
print(f"  Trigger delay:     {trigger_delay} seconds")
print(f"  OUT2 triggered after delay")
print(f"  Approx phase shift: {phase_shift_deg:.1f}°")
print()
print("Note: Channels triggered independently to create phase offset")
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

# Configure burst mode for Channel 1
rp.rp_GenMode(channel, rp.RP_GEN_MODE_BURST)
rp.rp_GenBurstCount(channel, ncyc)
rp.rp_GenBurstRepetitions(channel, nor)
rp.rp_GenBurstPeriod(channel, period)
print(f"  Burst mode configured: {ncyc} cycles, {nor} repetitions")


# Configure Channel 2 (OUT2)
print("\nConfiguring OUT2...")
rp.rp_GenWaveform(channel2, waveform)
print(f"  Waveform type set: {waveform}")

rp.rp_GenFreqDirect(channel2, freq)
print(f"  Frequency set: {freq} Hz")

rp.rp_GenAmp(channel2, ampl)
print(f"  Amplitude set: {ampl} V")

# Configure burst mode for Channel 2
rp.rp_GenMode(channel2, rp.RP_GEN_MODE_BURST)
rp.rp_GenBurstCount(channel2, ncyc)
rp.rp_GenBurstRepetitions(channel2, nor)
rp.rp_GenBurstPeriod(channel2, period)
print(f"  Burst mode configured: {ncyc} cycles, {nor} repetitions")


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
# ASYNCHRONOUS OUTPUT - Enable and trigger channels independently
# ==============================================================================

print("\nEnabling output and triggering channels asynchronously...")

# Enable output synchronization (required for proper operation)
rp.rp_GenOutEnableSync(True)
print("Output synchronization enabled")

# Enable output channel 1
rp.rp_GenOutEnable(channel)
print("OUT1 enabled")

# Allow settling time
time.sleep(0.1)

# Trigger Channel 1 first
print("\nTriggering OUT1...")
rp.rp_GenTriggerOnly(channel)
print("OUT1 triggered - burst started")

# Wait before triggering Channel 2
print(f"Waiting {trigger_delay} seconds before triggering OUT2...")
time.sleep(trigger_delay)

# Trigger Channel 2
print("Triggering OUT2...")
rp.rp_GenTriggerOnly(channel2)
print("OUT2 triggered - burst started (with phase offset)")

# Wait for bursts to complete
time.sleep(trigger_delay)

# Finally, synchronize and trigger both channels together
print("\nSynchronizing channels and triggering together...")
rp.rp_GenSynchronise()
rp.rp_GenTriggerOnly(channel)
print("Both channels synchronized and triggered")

print("\n" + "=" * 70)
print("Asynchronous signal generation demonstration complete!")
print(f"OUT1 and OUT2 were triggered with {trigger_delay}s delay")
print(f"This created an approximate phase shift of {phase_shift_deg:.1f}°")
print("Connect oscilloscope to both channels to observe phase relationship")
print("=" * 70)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing Red Pitaya resources...")

# Release resources and stop generation
rp.rp_Release()
print("Resources released - generation stopped")
print("\nProgram completed successfully")
