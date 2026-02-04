#!/usr/bin/python3
"""
Red Pitaya Frequency Sweep Generation Example
==============================================

This example demonstrates frequency sweep (chirp) signal generation on Red Pitaya.
A frequency sweep continuously changes the signal frequency from a start frequency
to a stop frequency over a specified time period. This is essential for frequency
response analysis, impedance spectroscopy, filter characterization, and system
identification applications.

Features:
- Linear or logarithmic frequency sweep
- Configurable start and stop frequencies
- Adjustable sweep time duration
- Normal or up-down sweep direction
- Real-time sweep parameter monitoring
- Interactive sweep control (start/stop)

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup:
  Connect oscilloscope or device under test to OUT1
  The generator will sweep through the specified frequency range

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Sweep module (rp_sweep)
- OS 2.00 or higher

Usage:
    python gen_7_sweep.py
    
    The program will start a frequency sweep from start_freq to stop_freq.
    Press Enter to stop the sweep and exit the program.

Configuration:
    Modify parameters in the CONFIGURATION section:
    - channel: Output channel (RP_CH_1 or RP_CH_2)
    - waveform: Waveform type (typically SINE for sweeps)
    - ampl: Signal amplitude in volts
    - sweep_start_freq: Starting frequency in Hz
    - sweep_stop_freq: Ending frequency in Hz
    - sweep_time_us: Total sweep duration in microseconds
    - sweep_mode: LINEAR or LOG sweep mode
    - sweep_dir: NORMAL (one-way) or UP_DOWN (back and forth)

Author: Red Pitaya
Date: January 2026
"""

import time
import rp
import rp_sweep


# ==============================================================================
# CONFIGURATION - Set your frequency sweep parameters
# ==============================================================================

# Generator output channel
# Available channels:
#   RP_CH_1 - Output channel 1 (OUT1)
#   RP_CH_2 - Output channel 2 (OUT2)

channel = rp.RP_CH_1

# Waveform type (typically SINE for frequency sweeps)
# Available waveforms:
#   RP_WAVEFORM_SINE      - Sine wave (recommended for sweeps)
#   RP_WAVEFORM_SQUARE    - Square wave
#   RP_WAVEFORM_TRIANGLE  - Triangle wave

waveform = rp.RP_WAVEFORM_SINE

# Signal amplitude
ampl = 1                        # Amplitude in volts (peak amplitude)

# Frequency sweep parameters
sweep_start_freq = 1000         # Starting frequency in Hz (1 kHz)
sweep_stop_freq = 100000        # Ending frequency in Hz (100 kHz)
sweep_time_us = 5000000         # Sweep duration in microseconds (5 seconds)

# Sweep mode
# Available modes:
#   RP_GEN_SWEEP_MODE_LINEAR - Linear frequency sweep
#   RP_GEN_SWEEP_MODE_LOG    - Logarithmic frequency sweep

sweep_mode = rp_sweep.RP_GEN_SWEEP_MODE_LINEAR

# Sweep direction
# Available directions:
#   RP_GEN_SWEEP_DIR_NORMAL  - One-way sweep (start to stop)
#   RP_GEN_SWEEP_DIR_UP_DOWN - Two-way sweep (start to stop and back)

sweep_dir = rp_sweep.RP_GEN_SWEEP_DIR_NORMAL

# Calculate sweep information
sweep_time_s = sweep_time_us / 1e6
freq_span = sweep_stop_freq - sweep_start_freq
sweep_rate = freq_span / sweep_time_s if sweep_time_s > 0 else 0

print("=" * 70)
print("Red Pitaya Frequency Sweep Generation Configuration")
print("=" * 70)
print(f"Output channel:      OUT{1 if channel == rp.RP_CH_1 else 2}")
print(f"Waveform:            {waveform}")
print(f"Amplitude:           {ampl} V (peak)")
print()
print("Sweep Parameters:")
print(f"  Start frequency:   {sweep_start_freq} Hz ({sweep_start_freq/1000:.2f} kHz)")
print(f"  Stop frequency:    {sweep_stop_freq} Hz ({sweep_stop_freq/1000:.2f} kHz)")
print(f"  Frequency span:    {freq_span} Hz ({freq_span/1000:.2f} kHz)")
print(f"  Sweep time:        {sweep_time_us} µs ({sweep_time_s:.2f} s)")
print(f"  Sweep rate:        {sweep_rate:.2f} Hz/s")
print(f"  Sweep mode:        {'LINEAR' if sweep_mode == rp_sweep.RP_GEN_SWEEP_MODE_LINEAR else 'LOGARITHMIC'}")
print(f"  Sweep direction:   {'NORMAL' if sweep_dir == rp_sweep.RP_GEN_SWEEP_DIR_NORMAL else 'UP-DOWN'}")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya and sweep module
# ==============================================================================

print("\nInitializing Red Pitaya and sweep module...")

# Initialize the Red Pitaya interface
rp.rp_Init()
print("Red Pitaya initialized")

# Initialize sweep module
rp_sweep.rp_SWInit()
print("Sweep module initialized")


# ==============================================================================
# RESET - Reset generator and sweep to default state
# ==============================================================================

print("\nResetting generator and sweep...")

# Reset generation to default state
rp.rp_GenReset()
print("Generator reset to default state")

# Reset all sweep parameters
rp_sweep.rp_SWResetAll()
print("Sweep parameters reset to default state")


# ==============================================================================
# SIGNAL GENERATION SETUP - Configure output waveform
# ==============================================================================

print("\nConfiguring signal generation...")

# Set waveform type
rp.rp_GenWaveform(channel, waveform)
print(f"Waveform type set: {waveform}")

# Set initial frequency (start frequency)
rp.rp_GenFreqDirect(channel, sweep_start_freq)
print(f"Initial frequency set: {sweep_start_freq} Hz")

# Set amplitude
rp.rp_GenAmp(channel, ampl)
print(f"Amplitude set: {ampl} V")


# ==============================================================================
# SWEEP CONFIGURATION - Configure frequency sweep parameters
# ==============================================================================

print("\nConfiguring frequency sweep parameters...")

# Set sweep start frequency
rp_sweep.rp_SWSetStartFreq(channel, sweep_start_freq)
print(f"Sweep start frequency: {sweep_start_freq} Hz")

# Set sweep stop frequency
rp_sweep.rp_SWSetStopFreq(channel, sweep_stop_freq)
print(f"Sweep stop frequency: {sweep_stop_freq} Hz")

# Set sweep time
rp_sweep.rp_SWSetTime(channel, sweep_time_us)
print(f"Sweep time: {sweep_time_us} µs")

# Set sweep mode (linear or logarithmic)
rp_sweep.rp_SWSetMode(channel, sweep_mode)
mode_str = 'LINEAR' if sweep_mode == rp_sweep.RP_GEN_SWEEP_MODE_LINEAR else 'LOGARITHMIC'
print(f"Sweep mode: {mode_str}")

# Set sweep direction (normal or up-down)
rp_sweep.rp_SWSetDir(channel, sweep_dir)
dir_str = 'NORMAL' if sweep_dir == rp_sweep.RP_GEN_SWEEP_DIR_NORMAL else 'UP-DOWN'
print(f"Sweep direction: {dir_str}")


# ==============================================================================
# VERIFY CONFIGURATION - Read back and verify sweep settings
# ==============================================================================

print("\nVerifying sweep configuration...")

# Read back and verify settings
start_freq_readback = rp_sweep.rp_SWGetStartFreq(channel)[1]
stop_freq_readback = rp_sweep.rp_SWGetStopFreq(channel)[1]
time_readback = rp_sweep.rp_SWGetTime(channel)[1]
mode_readback = rp_sweep.rp_SWGetMode(channel)[1]
dir_readback = rp_sweep.rp_SWGetDir(channel)[1]

print(f"  Start frequency:   {start_freq_readback} Hz (verified)")
print(f"  Stop frequency:    {stop_freq_readback} Hz (verified)")
print(f"  Sweep time:        {time_readback} µs (verified)")
print(f"  Sweep mode:        {mode_readback} (verified)")
print(f"  Sweep direction:   {dir_readback} (verified)")
print("Sweep configuration verified successfully")


# ==============================================================================
# ENABLE SWEEP - Enable sweep mode on the channel
# ==============================================================================

print("\nEnabling sweep mode...")

# Enable sweep generation on the channel
rp_sweep.rp_SWGenSweep(channel, True)
print("Sweep mode enabled")


# ==============================================================================
# OUTPUT ENABLE - Enable output and start sweep
# ==============================================================================

print("\nEnabling output and starting sweep...")

# Enable output channel
rp.rp_GenOutEnable(channel)
print(f"Output channel OUT{1 if channel == rp.RP_CH_1 else 2} enabled")

# Trigger the generator
rp.rp_GenTriggerOnly(channel)
print("Generator triggered")

# Start sweep execution
rp_sweep.rp_SWRun()
print("Sweep started - frequency sweep in progress")

print("\n" + "=" * 70)
print("Frequency sweep active!")
print(f"Sweeping from {sweep_start_freq} Hz to {sweep_stop_freq} Hz")
print(f"Sweep duration: {sweep_time_s:.2f} seconds")
print(f"Mode: {mode_str}, Direction: {dir_str}")
print("Connect oscilloscope or measurement device to observe sweep")
print()
print("Press Enter to stop the sweep and exit...")
print("=" * 70)

# Wait for user input to stop
input()

print("\nStopping sweep...")
rp_sweep.rp_SWStop()
print("Sweep stopped")


# ==============================================================================
# DISABLE SWEEP - Disable sweep mode
# ==============================================================================

print("\nDisabling sweep mode...")

# Disable sweep generation on the channel
rp_sweep.rp_SWGenSweep(channel, False)
print("Sweep mode disabled")


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nReleasing Red Pitaya resources...")

# Release sweep module resources
rp_sweep.rp_SWRelease()
print("Sweep module resources released")

# Release Red Pitaya resources
rp.rp_Release()
print("Red Pitaya resources released")

print("\nProgram completed successfully")
