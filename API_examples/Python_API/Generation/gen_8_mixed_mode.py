#!/usr/bin/python3
"""
Red Pitaya Mixed-Mode Dual-Channel Generation Example
=====================================================

This example demonstrates using two channels in different generation modes
simultaneously: one channel in continuous mode and the other in burst mode.
This is useful when you need a stable reference signal on one channel while
the other generates timed pulses.

Features:
- OUT1 and OUT2 both configured initially with the same waveform
- One channel (burst_ch) then switched to burst mode
- Synchronized enable and trigger for both channels
- Independent re-trigger capability for individual or both channels

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup:
  Connect oscilloscope or measurement device to OUT1 and OUT2.
  OUT1 will output a continuous sine wave while OUT2 generates bursts
  (or vice versa, depending on the burst_ch setting).

Software Requirements:
- Red Pitaya Python API (rp module)
- OS 2.00 or higher

Usage:
    python gen_8_mixed_mode.py

    The program will:
    1. Configure both channels with the same base waveform
    2. Switch the burst channel to burst mode
    3. Enable and trigger both channels simultaneously
    4. Re-trigger channel 0 individually after a delay
    5. Re-trigger both channels simultaneously after another delay

Configuration:
    Modify parameters in the CONFIGURATION section:
    - channel: List of output channels (both CH_1 and CH_2)
    - waveform: Waveform type applied to both channels initially
    - freq: Signal frequency in Hz
    - ampl: Signal amplitude in volts
    - burst_ch: Channel to switch into burst mode
    - ncyc: Number of waveform cycles per burst
    - nor: Number of burst repetitions
    - period: Time between burst starts in microseconds

Author: Red Pitaya
Date: January 2026
"""

import time
import rp


# ==============================================================================
# CONFIGURATION - Set your mixed-mode generation parameters
# ==============================================================================

# Generator output channels (both channels receive the base waveform)
# Available channels:
#   RP_CH_1 - Output channel 1 (OUT1)
#   RP_CH_2 - Output channel 2 (OUT2)

channel = [rp.RP_CH_1, rp.RP_CH_2]

# Waveform type (applied to both channels initially)
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

# Signal parameters (applied to both channels)
freq = 1e6      # Frequency in Hz (1 MHz)
ampl = 1        # Amplitude in volts (peak amplitude)

# Channel to switch to burst mode (the other stays in continuous mode)
# Available channels:
#   RP_CH_1 - Burst mode on OUT1, continuous on OUT2
#   RP_CH_2 - Burst mode on OUT2, continuous on OUT1

burst_ch = rp.RP_CH_1

# Burst mode parameters for the burst channel
ncyc   = 3      # Number of waveform cycles per burst
nor    = 2      # Number of burst repetitions
period = 10     # Time from start of one burst repetition to the next (µs).
                # Must be >= burst duration: ncyc / freq * 1e6

# Calculate burst timing information
burst_duration_us = (ncyc / freq) * 1e6  # Duration of one burst in microseconds
cont_ch = channel[1] if burst_ch == rp.RP_CH_1 else channel[0]

print("=" * 70)
print("Red Pitaya Mixed-Mode Dual-Channel Generation Configuration")
print("=" * 70)
print(f"Waveform:            {waveform}")
print(f"Frequency:           {freq:.0f} Hz")
print(f"Amplitude:           {ampl} V (peak)")
print()
print("Channel Modes:")
print(f"  Burst channel:     OUT{1 if burst_ch == rp.RP_CH_1 else 2}")
print(f"  Continuous channel: OUT{2 if burst_ch == rp.RP_CH_1 else 1}")
print()
print("Burst Mode Parameters:")
print(f"  Cycles per burst:  {ncyc}")
print(f"  Burst repetitions: {nor}")
print(f"  Burst period:      {period} µs")
print(f"  Burst duration:    {burst_duration_us:.2f} µs")
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
# SIGNAL GENERATION SETUP - Configure base waveform on both channels
# ==============================================================================

print("\nConfiguring base waveform on both channels...")

for ch in channel:
    ch_label = f"OUT{1 if ch == rp.RP_CH_1 else 2}"
    rp.rp_GenWaveform(ch, waveform)
    rp.rp_GenFreqDirect(ch, freq)
    rp.rp_GenAmp(ch, ampl)
    print(f"  {ch_label}: {waveform}, {freq:.0f} Hz, {ampl} V")

print("Base waveform applied to both channels")


# ==============================================================================
# BURST MODE CONFIGURATION - Switch burst channel to burst mode
# ==============================================================================

print(f"\nSwitching OUT{1 if burst_ch == rp.RP_CH_1 else 2} to burst mode...")

# Switch the designated channel to burst mode
rp.rp_GenMode(burst_ch, rp.RP_GEN_MODE_BURST)
print(f"Generator mode set: BURST")

# Set number of cycles per burst
rp.rp_GenBurstCount(burst_ch, ncyc)
print(f"Cycles per burst: {ncyc}")

# Set number of burst repetitions
rp.rp_GenBurstRepetitions(burst_ch, nor)
print(f"Burst repetitions: {nor}")

# Set burst period (time between burst starts)
rp.rp_GenBurstPeriod(burst_ch, period)
print(f"Burst period: {period} µs")

print("Burst mode configured")


# ==============================================================================
# OUTPUT ENABLE - Enable and trigger both channels simultaneously
# ==============================================================================

print("\nEnabling and triggering both channels simultaneously...")

# Enable both outputs and synchronize start
rp.rp_GenOutEnableSync(True)
rp.rp_GenSynchronise()
print("Both channels enabled and synchronized")

time.sleep(5)

# Re-trigger the first channel only (demonstrates individual channel control)
rp.rp_GenTriggerOnly(channel[0])
print(f"OUT{1 if channel[0] == rp.RP_CH_1 else 2} re-triggered individually")

time.sleep(5)

# Re-trigger both channels simultaneously using the combined trigger
rp.rp_GenTriggerOnlyBoth()
print("Both channels re-triggered simultaneously")

print("\n" + "=" * 70)
print("Mixed-mode generation active!")
print(f"OUT{1 if cont_ch == rp.RP_CH_1 else 2}: Continuous {waveform} at {freq:.0f} Hz")
print(f"OUT{1 if burst_ch == rp.RP_CH_1 else 2}: Burst mode, {ncyc} cycles × {nor} repetitions")
print("=" * 70)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing Red Pitaya resources...")

# Release resources and stop generation
rp.rp_Release()
print("Resources released - generation stopped")
print("\nProgram completed successfully")
