#!/usr/bin/python3
"""
Red Pitaya External Trigger Burst Generation Example
=====================================================

This example demonstrates burst mode signal generation triggered by an external
trigger signal on Red Pitaya. The generator waits for an external trigger event
before outputting each burst, allowing synchronization with external equipment
or events. This is useful for synchronized measurements, triggered pulse generation,
and event-based signal generation.

Features:
- External trigger-based burst generation
- Configurable trigger edge (positive or negative)
- Debounce filter for trigger signal
- Multiple waveform types supported
- Adjustable burst parameters

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup:
  1. Connect oscilloscope or measurement device to OUT1
  2. Connect external trigger source to EXT TRIG input (DIO0_P pin)
  3. The generator will output a burst each time the trigger event occurs

Software Requirements:
- Red Pitaya Python API (rp module)
- OS 2.00 or higher

Usage:
    python gen_3_sig_ext_trig.py
    
    The program configures the generator in external trigger mode and waits
    for trigger events. Each trigger will produce the configured burst.

Configuration:
    Modify parameters in the CONFIGURATION section:
    - channel: Output channel (RP_CH_1 or RP_CH_2)
    - waveform: Waveform type (SINE, SQUARE, etc.)
    - freq: Signal frequency in Hz
    - ampl: Signal amplitude in volts
    - ncyc: Number of waveform periods per burst
    - nor: Number of burst repetitions per trigger
    - period: Time between burst starts in microseconds
    - gen_trig_sour: Trigger source (EXT_PE or EXT_NE)
    - debounce_len: Trigger debounce filter length in microseconds

Author: Red Pitaya
Date: January 2026
"""

import time
import rp


# ==============================================================================
# CONFIGURATION - Set your external trigger burst generation parameters
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

waveform = rp.RP_WAVEFORM_SQUARE

# Signal parameters
freq = 1000000                  # Frequency in Hz (1 MHz)
ampl = 1                        # Amplitude in volts (peak amplitude)

# Burst mode parameters
ncyc = 4                        # Number of waveform periods in one burst
nor = 2                         # Number of repeated bursts per trigger
period = 300                    # Delay between start of consecutive bursts
                                # in microseconds (300 µs)

# External trigger parameters
debounce_len = 0                # Debounce filter length in microseconds
                                # (minimum of 1 µs, 0 = disabled)
                                # Filters out trigger signal noise

# Generator mode
# Available modes:
#   RP_GEN_MODE_CONTINUOUS - Continuous waveform generation
#   RP_GEN_MODE_BURST      - Burst mode (repeated signal bursts)
#   RP_GEN_MODE_STREAM     - Streaming mode

mode = rp.RP_GEN_MODE_BURST

# Generator trigger source
# Available trigger sources:
#   RP_GEN_TRIG_SRC_INTERNAL - Internal trigger (immediate)
#   RP_GEN_TRIG_SRC_EXT_PE   - External trigger positive edge
#   RP_GEN_TRIG_SRC_EXT_NE   - External trigger negative edge

gen_trig_sour = rp.RP_GEN_TRIG_SRC_EXT_PE

# Calculate burst timing information
burst_duration_us = (ncyc / freq) * 1e6  # Duration of one burst in microseconds
total_burst_time = (period * (nor - 1)) + burst_duration_us if nor > 0 else burst_duration_us

print("=" * 70)
print("Red Pitaya External Trigger Burst Generation Configuration")
print("=" * 70)
print(f"Output channel:      OUT{1 if channel == rp.RP_CH_1 else 2}")
print(f"Waveform:            {waveform}")
print(f"Frequency:           {freq} Hz ({freq/1e6:.2f} MHz)")
print(f"Amplitude:           {ampl} V (peak)")
print()
print("Burst Mode Parameters:")
print(f"  Cycles per burst:  {ncyc}")
print(f"  Burst repetitions: {nor}")
print(f"  Burst period:      {period} µs")
print(f"  Burst duration:    {burst_duration_us:.2f} µs")
print(f"  Total burst time:  {total_burst_time:.2f} µs")
print()
print("External Trigger Configuration:")
trigger_type = "Positive Edge" if gen_trig_sour == rp.RP_GEN_TRIG_SRC_EXT_PE else "Negative Edge"
print(f"  Trigger source:    External ({trigger_type})")
print(f"  Debounce filter:   {debounce_len} µs {'(disabled)' if debounce_len == 0 else ''}")
print()
print("SETUP: Connect external trigger source to EXT TRIG input (DIO0_P)")
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
# EXTERNAL TRIGGER CONFIGURATION - Configure trigger settings
# ==============================================================================

print("\nConfiguring external trigger...")

# Set length of internal debounce filter
# Minimum of 1 µs, 0 to disable
rp.rp_GenSetExtTriggerDebouncerUs(debounce_len)
print(f"Trigger debounce filter: {debounce_len} µs")

# Specify generator trigger source
rp.rp_GenTriggerSource(channel, gen_trig_sour)
trigger_type = "External Positive Edge" if gen_trig_sour == rp.RP_GEN_TRIG_SRC_EXT_PE else "External Negative Edge"
print(f"Trigger source set: {trigger_type}")


# ==============================================================================
# OUTPUT ENABLE - Enable output and arm for trigger
# ==============================================================================

print("\nEnabling output and arming for trigger...")

# Enable output channel
rp.rp_GenOutEnable(channel)
print(f"Output channel OUT{1 if channel == rp.RP_CH_1 else 2} enabled")

print("\n" + "=" * 70)
print("Generator armed and waiting for external trigger!")
print(f"Each trigger will generate {nor} burst(s) of {ncyc} cycle(s)")
print(f"Trigger input: EXT TRIG (DIO0_P) - {trigger_type}")
print(f"Connect oscilloscope to OUT{1 if channel == rp.RP_CH_1 else 2} to observe the bursts")
print("=" * 70)
print("\nNote: Generator is now armed and will respond to external triggers")
print("      Apply trigger signals to EXT TRIG input to generate bursts")


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing Red Pitaya resources...")

# Release resources and stop generation
rp.rp_Release()
print("Resources released - generator stopped")
print("\nProgram completed successfully")
