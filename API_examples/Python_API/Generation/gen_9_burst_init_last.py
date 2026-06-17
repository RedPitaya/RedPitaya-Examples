#!/usr/bin/python3
"""
Red Pitaya Burst Generation with Initial and Last Value Example
===============================================================

This example demonstrates burst mode generation where the output voltage
before the first burst and between/after bursts can be set to custom DC
levels. This is useful for controlling the quiescent state of a DUT
(Device Under Test) or for generating pre-charged pulse sequences.

Features:
- Single-channel burst mode generation
- Configurable initial voltage that appears before the first burst starts
- Configurable "last" voltage that appears between bursts and after the final burst
- Configurable burst parameters (cycles, repetitions, period)

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup:
  Connect oscilloscope or measurement device to OUT1.
  The output will hold the initial voltage, then burst, then hold the last voltage
  between repetitions and after the final burst completes.

Software Requirements:
- Red Pitaya Python API (rp module)
- OS 2.00 or higher

Usage:
    python gen_9_burst_init_last.py

    The program will:
    1. Configure the channel in burst mode with specified waveform parameters
    2. Set the initial voltage level held before the first burst fires
    3. Set the last voltage level held between bursts and after the final burst
    4. Enable the output and trigger the burst sequence

Configuration:
    Modify parameters in the CONFIGURATION section:
    - channel: Output channel (RP_CH_1 or RP_CH_2)
    - waveform: Waveform type (SINE, SQUARE, etc.)
    - freq: Signal frequency in Hz
    - ampl: Signal amplitude in volts
    - ncyc: Number of waveform cycles per burst
    - nor: Number of burst repetitions
    - period: Time between burst starts in microseconds
    - init_ampl: DC voltage before the first burst fires (V)
    - last_ampl: DC voltage between bursts and after the last burst (V)

Note:
    init_ampl sets the output level BEFORE the first burst is triggered.
    last_ampl sets the output level BETWEEN burst repetitions and AFTER the
    final burst completes. Both values are in Volts and must be within the
    output range of the Red Pitaya (typically ±1 V at 1:1 attenuation).

Author: Red Pitaya
Date: January 2026
"""

import rp


# ==============================================================================
# CONFIGURATION - Set your burst generation parameters
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
freq = 1e6      # Frequency in Hz (1 MHz)
ampl = 1        # Amplitude in volts (peak amplitude during the burst)

# Burst mode parameters
ncyc   = 1      # Number of waveform cycles per burst
nor    = 3      # Number of burst repetitions
period = 5      # Time from the start of one burst to the start of the next (µs).
                # Must be >= burst duration: ncyc / freq * 1e6 = 1 µs here

# Quiescent voltage levels
init_ampl = 0.5     # Voltage held at the output BEFORE the first burst fires (V)
last_ampl = 1.0     # Voltage held BETWEEN burst repetitions and AFTER the last burst (V)

# Generator mode
# Available modes:
#   RP_GEN_MODE_CONTINUOUS - Continuous waveform generation
#   RP_GEN_MODE_BURST      - Burst mode (repeated signal bursts)
#   RP_GEN_MODE_STREAM     - Streaming mode

mode = rp.RP_GEN_MODE_BURST

# Calculate burst timing information
burst_duration_us = (ncyc / freq) * 1e6  # Duration of one burst in microseconds

print("=" * 70)
print("Red Pitaya Burst Generation with Init/Last Values Configuration")
print("=" * 70)
print(f"Output channel:      OUT{1 if channel == rp.RP_CH_1 else 2}")
print(f"Waveform:            {waveform}")
print(f"Frequency:           {freq:.0f} Hz")
print(f"Amplitude:           {ampl} V (peak)")
print()
print("Burst Mode Parameters:")
print(f"  Cycles per burst:  {ncyc}")
print(f"  Burst repetitions: {nor}")
print(f"  Burst period:      {period} µs")
print(f"  Burst duration:    {burst_duration_us:.2f} µs")
print()
print("Quiescent Levels:")
print(f"  Initial voltage:   {init_ampl} V  (before first burst)")
print(f"  Last voltage:      {last_ampl} V  (between/after bursts)")
print("=" * 70)

if period < burst_duration_us:
    print(f"\nWARNING: Burst period ({period} µs) is shorter than burst duration "
          f"({burst_duration_us:.2f} µs). Increase 'period' to avoid overlap.")


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
# SIGNAL GENERATION SETUP - Configure waveform parameters
# ==============================================================================

print("\nConfiguring signal generation...")

# Set waveform type
rp.rp_GenWaveform(channel, waveform)
print(f"Waveform type set: {waveform}")

# Set frequency using direct method
rp.rp_GenFreqDirect(channel, freq)
print(f"Frequency set: {freq:.0f} Hz")

# Set amplitude
rp.rp_GenAmp(channel, ampl)
print(f"Amplitude set: {ampl} V")


# ==============================================================================
# BURST MODE CONFIGURATION - Configure burst parameters
# ==============================================================================

print("\nConfiguring burst mode parameters...")

# Set generator mode to burst
rp.rp_GenMode(channel, mode)
print("Generator mode set: BURST")

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
# INIT/LAST VOLTAGE CONFIGURATION - Set quiescent output levels
# ==============================================================================

print("\nConfiguring quiescent voltage levels...")

# Set the DC level present at the output BEFORE the first burst fires
rp.rp_GenSetInitGenValue(channel, init_ampl)
print(f"Initial voltage set: {init_ampl} V  (held before first burst)")

# Set the DC level present BETWEEN burst repetitions and AFTER the last burst
rp.rp_GenBurstLastValue(channel, last_ampl)
print(f"Last voltage set:    {last_ampl} V  (held between/after bursts)")


# ==============================================================================
# OUTPUT ENABLE - Enable output and start generation
# ==============================================================================

print("\nEnabling output and triggering burst sequence...")

# Enable output channel
rp.rp_GenOutEnable(channel)
print(f"Output channel OUT{1 if channel == rp.RP_CH_1 else 2} enabled")

# Trigger the generator to start the burst sequence
rp.rp_GenTriggerOnly(channel)
print("Generator triggered - burst sequence started")

print("\n" + "=" * 70)
print("Burst sequence active!")
print(f"Generating {nor} burst(s) of {ncyc} cycle(s) each on OUT{1 if channel == rp.RP_CH_1 else 2}")
print(f"Output holds {init_ampl} V before the first burst,")
print(f"then {last_ampl} V between repetitions and after the final burst")
print("=" * 70)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing Red Pitaya resources...")

# Release resources and stop generation
rp.rp_Release()
print("Resources released - generation stopped")
print("\nProgram completed successfully")
