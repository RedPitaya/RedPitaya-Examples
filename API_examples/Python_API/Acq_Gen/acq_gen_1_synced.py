#!/usr/bin/python3
"""
Red Pitaya Synchronized Acquisition and Generation Example
===========================================================

This example demonstrates synchronized signal generation and acquisition on Red Pitaya.
The generator outputs a burst waveform, and the acquisition is triggered by the generator's
output, ensuring perfect synchronization between generation and capture.

This is useful for testing signal processing, measuring system responses, or creating
synchronized stimulus-response measurements.

Features:
- Synchronized burst generation and acquisition
- Configurable waveform, frequency, and amplitude
- Burst mode with configurable cycle count and repetition
- Generator-triggered acquisition for perfect timing
- Buffer fill monitoring (OS 2.00+)
- Data output in volts

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Optional: Connect OUT1 to IN1 for loopback testing
- Optional: External circuit between generator output and input

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- OS 2.00 or higher (for buffer fill state monitoring)

Usage:
    python acq_gen_1_synced.py
    
    For loopback testing: Connect OUT1 to IN1 with a cable or jumper.
    The program will generate a burst and capture it synchronously.

Configuration:
    Modify parameters in the CONFIGURATION section:
    - waveform: Signal type (sine, square, triangle, etc.)
    - freq: Signal frequency in Hz
    - ampl: Signal amplitude in volts
    - ncyc: Number of cycles per burst
    - N: Number of samples to capture

Author: Red Pitaya
Date: May 2026
"""

import time
import numpy as np
import rp


# ==============================================================================
# CONFIGURATION - Set your synchronized acquisition and generation parameters
# ==============================================================================

# Generation parameters
channel = rp.RP_CH_1            # Output channel (RP_CH_1 or RP_CH_2)

# Waveform type
# Available waveforms:
#   RP_WAVEFORM_SINE, RP_WAVEFORM_SQUARE, RP_WAVEFORM_TRIANGLE, 
#   RP_WAVEFORM_RAMP_UP, RP_WAVEFORM_RAMP_DOWN, RP_WAVEFORM_DC, 
#   RP_WAVEFORM_PWM, RP_WAVEFORM_ARBITRARY, RP_WAVEFORM_DC_NEG, 
#   RP_WAVEFORM_SWEEP
waveform = rp.RP_WAVEFORM_SINE

freq = 100000                   # Frequency in Hz (100 kHz)
ampl = 1.0                      # Amplitude in volts

# Burst mode parameters
ncyc = 3                        # Number of cycles per burst
nor = 1                         # Number of repetitions (1 = single burst)
period = 10                     # Period between bursts in microseconds

# Trigger parameters
# Available generation trigger sources:
#   RP_GEN_TRIG_SRC_INTERNAL, RP_GEN_TRIG_SRC_EXT_PE, RP_GEN_TRIG_SRC_EXT_NE
gen_trig_sour = rp.RP_GEN_TRIG_SRC_INTERNAL

# Available acquisition trigger sources:
#   RP_TRIG_SRC_DISABLED, RP_TRIG_SRC_NOW, RP_TRIG_SRC_CHA_PE,
#   RP_TRIG_SRC_CHA_NE, RP_TRIG_SRC_CHB_PE, RP_TRIG_SRC_CHB_NE,
#   RP_TRIG_SRC_EXT_PE, RP_TRIG_SRC_EXT_NE, RP_TRIG_SRC_AWG_PE,
#   RP_TRIG_SRC_AWG_NE, RP_TRIG_SRC_CHC_PE, RP_TRIG_SRC_CHC_NE,
#   RP_TRIG_SRC_CHD_PE, RP_TRIG_SRC_CHD_NE, RP_TRIG_SRC_CHA_AE,
#   RP_TRIG_SRC_CHB_AE, RP_TRIG_SRC_EXT_AE, RP_TRIG_SRC_AWG_PE,
#   RP_TRIG_SRC_CHC_AE, RP_TRIG_SRC_CHD_AE

acq_trig_sour = rp.RP_TRIG_SRC_CHA_PE

# Available trigger channels (for trigger level):
#   RP_T_CH_1, RP_T_CH_2, RP_T_CH_3, RP_T_CH_4, RP_T_CH_EXT
acq_trig_channel = rp.RP_T_CH_1

trig_lvl = 0.5                  # Trigger level in volts
trig_dly = 0                    # Trigger delay in samples

# Acquisition parameters
# Available decimations: 1, 2, 4, 8, 16, 17, 18, ..., 65536
#   Decimation 1 = 125 MS/s
#   Decimation 8 = 15.625 MS/s
#   Sample rate = 125 MS/s / decimation
dec = 1                         # Decimation factor

buffer_size = 16384                       # Number of samples to capture

data_ch1 = np.zeros(buffer_size, dtype=np.float32)  # Pre-allocate NumPy array for channel 1 data

print("=" * 70)
print("Red Pitaya Synchronized Acquisition and Generation Configuration")
print("=" * 70)
print(f"Generator channel:   {channel}")
print(f"Waveform:            {waveform}")
print(f"Frequency:           {freq} Hz")
print(f"Amplitude:           {ampl} V")
print(f"Burst cycles:        {ncyc}")
print(f"Burst repetitions:   {nor}")
print(f"Burst period:        {period} µs")
print()
print(f"Decimation:          {dec} (Sample rate: {125000000 / dec / 1000000:.2f} MS/s)")
print(f"Samples to capture:  {buffer_size}")
print(f"Trigger level:       {trig_lvl} V")
print(f"Trigger delay:       {trig_dly} samples")
print(f"Gen trigger source:  {gen_trig_sour}")
print(f"Acq trigger source:  {acq_trig_sour}")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya
# ==============================================================================

print("\nInitializing Red Pitaya...")

# Initialize the Red Pitaya interface
rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# RESET - Reset generation and acquisition
# ==============================================================================

print("\nResetting generator and acquisition...")

# Reset generation and acquisition to default state
rp.rp_GenReset()
rp.rp_AcqReset()
print("Generator and acquisition reset to default state")


# ==============================================================================
# GENERATION SETUP - Configure signal generation
# ==============================================================================

print("\nConfiguring signal generation...")

# Set waveform type
rp.rp_GenWaveform(channel, waveform)
print(f"Waveform set to: {waveform}")

# Set frequency and amplitude
rp.rp_GenFreqDirect(channel, freq)
rp.rp_GenAmp(channel, ampl)
print(f"Frequency: {freq} Hz, Amplitude: {ampl} V")

# Configure burst mode
rp.rp_GenMode(channel, rp.RP_GEN_MODE_BURST)
rp.rp_GenBurstCount(channel, ncyc)              # Number of cycles per burst
rp.rp_GenBurstRepetitions(channel, nor)         # Number of repetitions
rp.rp_GenBurstPeriod(channel, period)           # Period between bursts
print(f"Burst mode: {ncyc} cycles, {nor} repetitions, {period} µs period")

# Specify generator trigger source
rp.rp_GenTriggerSource(channel, gen_trig_sour)
print(f"Generator trigger source: {gen_trig_sour}")

# Enable output synchronization and output
rp.rp_GenOutEnableSync(True)
print(f"Generator output enabled on {channel} with synchronization")


# ==============================================================================
# ACQUISITION SETUP - Configure data acquisition
# ==============================================================================

print("\nConfiguring data acquisition...")

# Set decimation factor
rp.rp_AcqSetDecimationFactor(dec)
print(f"Decimation: {dec} (Sample rate: {125000000 / dec / 1000000:.2f} MS/s)")

# Set trigger level and delay
rp.rp_AcqSetTriggerLevel(acq_trig_channel, trig_lvl)
rp.rp_AcqSetTriggerDelay(trig_dly)
print(f"Trigger level: {trig_lvl} V, Delay: {trig_dly} samples")

# Start acquisition
print("Starting acquisition...")
rp.rp_AcqStart()
print("Acquisition started")

# Set trigger source (AWG positive edge for synchronization)
rp.rp_AcqSetTriggerSrc(acq_trig_sour)
print(f"Acquisition trigger source: {acq_trig_sour}")


# ==============================================================================
# TRIGGER AND CAPTURE - Trigger generation and wait for acquisition
# ==============================================================================

print("\nTriggering generation...")

# Trigger the generator
rp.rp_GenTriggerOnly(channel)
print("Generator triggered")

# Check trigger state
trigger_state = rp.rp_AcqGetTriggerState()[1]
print(f"Initial trigger state: {trigger_state}")

# Wait for trigger event
print("Waiting for acquisition trigger...")
while True:
    trig_state = rp.rp_AcqGetTriggerState()[1]
    if trig_state == rp.RP_TRIG_STATE_TRIGGERED:
        print("Acquisition triggered!")
        break

# Check buffer fill state (OS 2.00 or higher only)
fill_state = rp.rp_AcqGetBufferFillState()[1]
print(f"Buffer fill state: {fill_state}")

# Wait for buffer to fill (OS 2.00 or higher only)
print("Waiting for buffer to fill...")
while True:
    if rp.rp_AcqGetBufferFillState()[1]:
        print("Buffer filled!")
        break


# ==============================================================================
# DATA RETRIEVAL - Read captured data
# ==============================================================================

print("\nRetrieving captured data...")

# Allocate buffer for voltage data


# Get data in volts from channel 1
res = rp.rp_AcqGetDataVNP(rp.RP_CH_1, buffer_size, data_ch1)


print(f"Retrieved {buffer_size} samples from CH1")
print(f"Data range: {data_ch1.min():.6f} V to {data_ch1.max():.6f} V")
print(f"Mean value: {data_ch1.mean():.6f} V")

# Display first 10 samples as example
print("\nFirst 10 samples (in volts):")
for i in range(min(10, buffer_size)):
    print(f"  Sample [{i}]: {data_ch1[i]:.6f} V")


# ==============================================================================
# DATA OUTPUT - Display full data array
# ==============================================================================

print("\nFull data array:")
print(data_ch1)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nCleaning up...")

# Release Red Pitaya resources
rp.rp_Release()

print("Resources released - program complete")
print("\nNote: Data has been captured and displayed above")
print("      For further analysis, save data_ch1 array to a file or plot it")
