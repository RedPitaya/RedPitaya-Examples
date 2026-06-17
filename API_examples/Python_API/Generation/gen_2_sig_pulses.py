#!/usr/bin/python3
"""
Red Pitaya Burst Mode Signal Generation Example
================================================

This example demonstrates burst mode signal generation on Red Pitaya.
In burst mode, the generator outputs a specified number of waveform periods
(one burst), then repeats this burst pattern at regular intervals. This is
useful for pulsed signal generation, radar applications, and testing systems
that respond to periodic pulses.

Features:
- Burst mode waveform generation
- Configurable number of cycles per burst
- Configurable number of burst repetitions
- Adjustable period between bursts
- Multiple waveform types supported

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup:
  Connect oscilloscope or measurement device to OUT1
  The generator will output signal bursts with specified timing

Software Requirements:
- Red Pitaya Python API (rp module)
- OS 2.00 or higher

Usage:
    python gen_2_sig_pulses.py
    
    The program will generate repeated bursts of the selected waveform
    on the output channel with configured timing parameters.

Configuration:
    Modify parameters in the CONFIGURATION section:
    - channel: Output channel (RP_CH_1 or RP_CH_2)
    - waveform: Waveform type (SINE, SQUARE, etc.)
    - freq: Signal frequency in Hz
    - ampl: Signal amplitude in volts
    - ncyc: Number of waveform periods per burst
    - nor: Number of burst repetitions
    - period: Time between burst starts in microseconds

Author: Red Pitaya
Date: January 2026
"""

import time
import rp


# ==============================================================================
# CONFIGURATION - Set your burst signal generation parameters
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
freq = 1000                     # Frequency in Hz (1 kHz)
ampl = 1                        # Amplitude in volts (peak amplitude)

# Burst mode parameters
ncyc = 1                        # Number of waveform periods in one burst
nor = 1000                      # Number of repeated bursts
period = 5000                   # Delay between start of consecutive bursts
                                # in microseconds (5000 µs = 5 ms)

# Generator mode
# Available modes:
#   RP_GEN_MODE_CONTINUOUS - Continuous waveform generation
#   RP_GEN_MODE_BURST      - Burst mode (repeated signal bursts)
#   RP_GEN_MODE_STREAM     - Streaming mode

mode = rp.RP_GEN_MODE_BURST

# Calculate burst timing information
burst_duration_us = (ncyc / freq) * 1e6  # Duration of one burst in microseconds
duty_cycle = (burst_duration_us / period) * 100 if period > 0 else 0

print("=" * 70)
print("Red Pitaya Burst Mode Signal Generation Configuration")
print("=" * 70)
print(f"Output channel:      OUT{1 if channel == rp.RP_CH_1 else 2}")
print(f"Waveform:            {waveform}")
print(f"Frequency:           {freq} Hz")
print(f"Amplitude:           {ampl} V (peak)")
print()
print("Burst Mode Parameters:")
print(f"  Cycles per burst:  {ncyc}")
print(f"  Burst repetitions: {nor}")
print(f"  Burst period:      {period} µs ({period/1000:.2f} ms)")
print(f"  Burst duration:    {burst_duration_us:.2f} µs")
print(f"  Duty cycle:        {duty_cycle:.2f}%")
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
# BURST MODE CONFIGURATION - Configure burst parameters
# ==============================================================================

print("\nConfiguring burst mode parameters...")

# Set generator mode to burst
rp.rp_GenMode(channel, mode)
print(f"Generator mode set: BURST")

# Set number of cycles per burst
rp.rp_GenBurstCount(channel, ncyc)
print(f"Cycles per burst: {ncyc}")

# Set number of burst repetitions
rp.rp_GenBurstRepetitions(channel, nor)
print(f"Burst repetitions: {nor}")

# Set burst period (time between burst starts)
rp.rp_GenBurstPeriod(channel, period)
print(f"Burst period: {period} µs")


# ==============================================================================
# OUTPUT ENABLE - Enable output and start generation
# ==============================================================================

print("\nEnabling output and starting burst generation...")

# Enable output channel
rp.rp_GenOutEnable(channel)
print(f"Output channel OUT{1 if channel == rp.RP_CH_1 else 2} enabled")

# Trigger the generator to start burst output
rp.rp_GenTriggerOnly(channel)
print("Generator triggered - burst mode signal output started")

print("\n" + "=" * 70)
print("Burst signal generation active!")
print(f"Generating {nor} bursts of {ncyc} cycle(s) each")
print(f"Burst period: {period} µs, Duty cycle: {duty_cycle:.2f}%")
print(f"Connect oscilloscope to OUT{1 if channel == rp.RP_CH_1 else 2} to observe the bursts")
print("=" * 70)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing Red Pitaya resources...")

# Release resources and stop generation
rp.rp_Release()
print("Resources released - burst generation stopped")
print("\nProgram completed successfully")
