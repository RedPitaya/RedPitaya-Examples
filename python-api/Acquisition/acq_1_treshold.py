#!/usr/bin/python3
"""
Red Pitaya Acquisition with Trigger Threshold Example
======================================================

This example demonstrates data acquisition with trigger threshold on Red Pitaya.
The acquisition waits for the input signal to cross a specified voltage threshold,
then captures data. This is useful for capturing events or analyzing signals that
occur when certain conditions are met.

Features:
- Threshold-based triggering on input channels
- Configurable trigger level and delay
- Captures data when signal crosses threshold
- Displays data in both volts and raw ADC values
- Optional signal generation for loopback testing

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup Options:
  Option 1 (External signal): 
    Connect external signal source to IN1
    
  Option 2 (Loopback test):
    Connect OUT1 to IN1 with a cable or jumper
    The example includes optional generation code for testing

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- OS 2.00 or higher (for buffer fill state monitoring)

Usage:
    python acq_1_threshold.py
    
    The program will wait for the input signal on IN1 to cross
    the trigger threshold (0.5V by default), then capture data.

Configuration:
    Modify parameters in the CONFIGURATION section:
    - trig_lvl: Trigger threshold voltage
    - acq_trig_sour: Trigger source (CHA_PE, CHA_NE, etc.)
    - dec: Decimation factor (affects sample rate)
    - N: Number of samples to capture

Author: Red Pitaya
Date: January 2026
"""

import time
import numpy as np
import rp


# ==============================================================================
# CONFIGURATION - Set your acquisition and trigger parameters
# ==============================================================================

# Acquisition parameters

channel = rp.RP_CH_1            # Acquisition channel (RP_CH_1 or RP_CH_2)

# Available decimations:
#   1,2,4,8,16,17,18,...,65536
dec = 1                         # Decimation factor

buff_size = 16384               # Number of samples to capture

# Trigger parameters
# Available acquisition trigger sources:
#   RP_TRIG_SRC_DISABLED - No trigger
#   RP_TRIG_SRC_NOW - Immediate trigger
#   RP_TRIG_SRC_CHA_PE - Channel A positive edge
#   RP_TRIG_SRC_CHA_NE - Channel A negative edge
#   RP_TRIG_SRC_CHB_PE - Channel B positive edge
#   RP_TRIG_SRC_CHB_NE - Channel B negative edge
#   RP_TRIG_SRC_EXT_PE - External trigger positive edge
#   RP_TRIG_SRC_EXT_NE - External trigger negative edge
#   RP_TRIG_SRC_AWG_PE - Generator positive edge
#   RP_TRIG_SRC_AWG_NE - Generator negative edge

acq_trig_sour = rp.RP_TRIG_SRC_CHA_PE

# Available trigger channels (for trigger level):
#   RP_T_CH_1, RP_T_CH_2, RP_T_CH_EXT

acq_trig_channel = rp.RP_T_CH_1     # Trigger channel for level setting

trig_lvl = 0.5                      # Trigger threshold level in volts
trig_dly = 0                        # Trigger delay in samples

# Optional: Signal generation parameters (for loopback testing)
# Set ENABLE_GENERATION = True to generate test signal on OUT1
# Connect OUT1 to IN1 for loopback testing
ENABLE_GENERATION = True

channel = rp.RP_CH_1            # Generator output channel
channel2 = rp.RP_CH_2           # Second generator output (optional)

waveform = rp.RP_WAVEFORM_SINE

freq = 100000                   # Generator frequency in Hz (100 kHz)
ampl = 1.0                      # Generator amplitude in volts

print("=" * 70)
print("Red Pitaya Acquisition with Trigger Threshold Configuration")
print("=" * 70)
print(f"Decimation:          {dec}")
print(f"Sample rate:         {125000000 / (2**int(np.log2(dec))) / 1000000:.2f} MS/s")
print(f"Samples to capture:  {buff_size}")
print(f"Trigger source:      {acq_trig_sour}")
print(f"Trigger level:       {trig_lvl} V")
print(f"Trigger delay:       {trig_dly} samples")
print()
if ENABLE_GENERATION:
    print("Signal Generation:   ENABLED (for loopback testing)")
    print(f"  Waveform:          {waveform}")
    print(f"  Frequency:         {freq} Hz")
    print(f"  Amplitude:         {ampl} V")
    print("  NOTE: Connect OUT1 to IN1 for loopback testing")
else:
    print("Signal Generation:   DISABLED")
    print("  NOTE: Connect external signal source to IN1")
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
# SIGNAL GENERATION SETUP (Optional - for loopback testing)
# ==============================================================================

if ENABLE_GENERATION:
    print("\nConfiguring signal generation (loopback test mode)...")
    
    # Configure OUT1
    rp.rp_GenWaveform(channel, waveform)
    rp.rp_GenFreq(channel, freq)
    rp.rp_GenAmp(channel, ampl)
    print(f"OUT1 configured: {waveform}, {freq} Hz, {ampl} V")
    
    # Configure OUT2 (optional - same settings)
    rp.rp_GenWaveform(channel2, waveform)
    rp.rp_GenFreq(channel2, freq)
    rp.rp_GenAmp(channel2, ampl)
    print(f"OUT2 configured: {waveform}, {freq} Hz, {ampl} V")
    
    # Set generator trigger source to internal
    rp.rp_GenTriggerSource(channel, rp.RP_GEN_TRIG_SRC_INTERNAL)
    
    # Enable output synchronization
    rp.rp_GenOutEnableSync(True)
    print("Generator output synchronization enabled")
else:
    print("\nSignal generation disabled - using external signal source")


# ==============================================================================
# ACQUISITION SETUP - Configure data acquisition
# ==============================================================================

print("\nConfiguring data acquisition...")

# Set decimation factor
rp.rp_AcqSetDecimationFactor(dec)
print(f"Decimation set to: {dec}")

# Set trigger level and delay
rp.rp_AcqSetTriggerLevel(acq_trig_channel, trig_lvl)
rp.rp_AcqSetTriggerDelay(trig_dly)
print(f"Trigger configured: Level = {trig_lvl} V, Delay = {trig_dly} samples")

# Start acquisition
print("Starting acquisition...")
rp.rp_AcqStart()
print("Acquisition started")

# Set trigger source
rp.rp_AcqSetTriggerSrc(acq_trig_sour)
print(f"Trigger source set to: {acq_trig_sour}")


# ==============================================================================
# TRIGGER AND CAPTURE - Trigger and wait for data capture
# ==============================================================================

print("\nWaiting for trigger event...")

if ENABLE_GENERATION:
    # Trigger the generator (creates signal for loopback)
    rp.rp_GenTriggerOnly(channel)
    print("Generator triggered (loopback mode)")

# Wait for trigger event
print("Monitoring for trigger threshold crossing...")
while True:
    trig_state = rp.rp_AcqGetTriggerState()[1]
    if trig_state == rp.RP_TRIG_STATE_TRIGGERED:
        print("Trigger event detected!")
        break

# Wait for buffer to fill (OS 2.00 or higher only)
print("Waiting for acquisition buffer to fill...")
while True:
    if rp.rp_AcqGetBufferFillState()[1]:
        print("Buffer filled - acquisition complete!")
        break


# ==============================================================================
# DATA RETRIEVAL - Read captured data
# ==============================================================================

print("\nRetrieving captured data...")

# Allocate buffers for raw and voltage data
data_ch_raw = np.zeros(buff_size, dtype=np.int16)
data_ch_V = np.zeros(buff_size, dtype=np.float32)

# Get trigger position
trig_pos = rp.rp_AcqGetWritePointerAtTrig()[1]

# Get raw ADC data
res = rp.rp_AcqGetDataRawNP(channel, trig_pos, buff_size, data_ch_raw)

# Get voltage data
res = rp.rp_AcqGetDataVNP(channel, trig_pos, buff_size, data_ch_V)

# Assign to variables for clarity
print(f"Retrieved {buff_size} samples from CH1")
print(f"Voltage range: {data_ch_V.min():.6f} V to {data_ch_V.max():.6f} V")
print(f"Raw ADC range: {data_ch_raw.min()} to {data_ch_raw.max()}")
print(f"Mean voltage: {data_ch_V.mean():.6f} V")

# Display first 10 samples as example
print("\nFirst 10 samples:")
print("  Sample | Voltage (V) | Raw ADC")
print("  " + "-" * 35)
for i in range(min(10, buff_size)):
    print(f"  {i:6d} | {data_ch_V[i]:11.6f} | {data_ch_raw[i]:7d}")


# ==============================================================================
# DATA OUTPUT - Display full data arrays
# ==============================================================================

print("\nFull data arrays:")
print(f"\nData in Volts:\n{data_ch_V}")
print(f"\nRaw ADC data:\n{data_ch_raw}")


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nCleaning up...")

# Release Red Pitaya resources
rp.rp_Release()

print("Resources released - program complete")
print("\nNote: Captured data is displayed above")
print("      For further analysis, save arrays to file or plot them")
