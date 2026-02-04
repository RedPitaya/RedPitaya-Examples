#!/usr/bin/python3
"""
Red Pitaya Instant Acquisition Example
=======================================

This example demonstrates immediate data acquisition on Red Pitaya without waiting
for a specific trigger condition. The acquisition starts immediately and captures
data continuously, making it useful for monitoring signals in real-time or capturing
data without specific trigger requirements.

Features:
- Immediate trigger mode (no waiting for threshold crossing)
- Captures data continuously from input channels
- Configurable decimation factor and sample count
- Simple, fast acquisition for monitoring applications
- Data output in volts

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Optional: Signal source connected to IN1 for testing

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- OS 2.00 or higher (for buffer fill state monitoring)

Usage:
    python acq_2_instant.py
    
    The program will immediately start capturing data from IN1
    without waiting for any trigger condition.

Configuration:
    Modify parameters in the CONFIGURATION section:
    - dec: Decimation factor (affects sample rate)
    - N: Number of samples to capture
    - acq_trig_sour: Trigger source (set to RP_TRIG_SRC_NOW for immediate)

Author: Red Pitaya
Date: January 2026
"""

import time
import numpy as np
import rp


# ==============================================================================
# CONFIGURATION - Set your instant acquisition parameters
# ==============================================================================

# Acquisition parameters
channel = rp.RP_CH_1            # Acquisition channel (RP_CH_1 or RP_CH_2)

# Available decimations:
#   1, 2, 4, 8, 16, 17, 18, ..., 65536
#   Decimation 1 = 125 MS/s
#   Decimation 8 = 15.625 MS/s
#   Sample rate = 125 MS/s / decimation
dec = 1                         # Decimation factor

buff_size = 16384               # Number of samples to capture

# Trigger parameters (for instant acquisition, use RP_TRIG_SRC_NOW)
# Available acquisition trigger sources:
#   RP_TRIG_SRC_DISABLED - No trigger
#   RP_TRIG_SRC_NOW - Immediate trigger (instant acquisition)
#   RP_TRIG_SRC_CHA_PE - Channel A positive edge
#   RP_TRIG_SRC_CHA_NE - Channel A negative edge
#   RP_TRIG_SRC_CHB_PE - Channel B positive edge
#   RP_TRIG_SRC_CHB_NE - Channel B negative edge
#   RP_TRIG_SRC_EXT_PE - External trigger positive edge
#   RP_TRIG_SRC_EXT_NE - External trigger negative edge
#   RP_TRIG_SRC_AWG_PE - Generator positive edge
#   RP_TRIG_SRC_AWG_NE - Generator negative edge

acq_trig_sour = rp.RP_TRIG_SRC_NOW

# Available trigger channels:
#   RP_T_CH_1, RP_T_CH_2, RP_T_CH_EXT
acq_trig_channel = rp.RP_T_CH_1     # Trigger channel for level setting

trig_lvl = 0.5                  # Trigger threshold level in volts (not used for NOW trigger)
trig_dly = 0                    # Trigger delay in samples

print("=" * 70)
print("Red Pitaya Instant Acquisition Configuration")
print("=" * 70)
print(f"Acquisition channel: {channel}")
print(f"Decimation:          {dec}")
print(f"Sample rate:         {125000000 / dec / 1000000:.2f} MS/s")
print(f"Samples to capture:  {buff_size}")
print(f"Trigger mode:        INSTANT (RP_TRIG_SRC_NOW)")
print(f"Trigger delay:       {trig_dly} samples")
print()
print("NOTE: Acquisition starts immediately without waiting for trigger")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya
# ==============================================================================

print("\nInitializing Red Pitaya...")

# Initialize the Red Pitaya interface
rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# RESET - Reset acquisition
# ==============================================================================

print("\nResetting acquisition...")

# Reset acquisition to default state
rp.rp_AcqReset()
print("Acquisition reset to default state")


# ==============================================================================
# ACQUISITION SETUP - Configure data acquisition
# ==============================================================================

print("\nConfiguring data acquisition...")

# Set decimation factor
rp.rp_AcqSetDecimationFactor(dec)
print(f"Decimation set to: {dec}")

# Set trigger level and delay (not critical for instant trigger)
rp.rp_AcqSetTriggerLevel(acq_trig_channel, trig_lvl)
rp.rp_AcqSetTriggerDelay(trig_dly)
print(f"Trigger parameters set (Level: {trig_lvl} V, Delay: {trig_dly} samples)")

# Start acquisition
print("Starting acquisition...")
rp.rp_AcqStart()
print("Acquisition started")

# Set trigger source to NOW (immediate trigger)
rp.rp_AcqSetTriggerSrc(acq_trig_sour)
print(f"Trigger source set to: {acq_trig_sour} (instant trigger)")


# ==============================================================================
# TRIGGER AND CAPTURE - Immediate trigger and data capture
# ==============================================================================

print("\nCapturing data immediately...")

# Wait for trigger event (should happen immediately with NOW trigger)
print("Waiting for trigger confirmation...")
while True:
    trig_state = rp.rp_AcqGetTriggerState()[1]
    if trig_state == rp.RP_TRIG_STATE_TRIGGERED:
        print("Trigger confirmed - capturing data!")
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

# Allocate buffer for voltage data
data_ch_V = np.zeros(buff_size, dtype=np.float32)

# Get trigger position
trig_pos = rp.rp_AcqGetWritePointerAtTrig()[1]

# Get voltage data using NumPy-based function
res = rp.rp_AcqGetDataVNP(channel, trig_pos, buff_size, data_ch_V)

print(f"Retrieved {buff_size} samples from {channel}")
print(f"Voltage range: {data_ch_V.min():.6f} V to {data_ch_V.max():.6f} V")
print(f"Mean voltage: {data_ch_V.mean():.6f} V")

# Display first 10 samples as example
print("\nFirst 10 samples (in volts):")
for i in range(min(10, buff_size)):
    print(f"  Sample [{i}]: {data_ch_V[i]:.6f} V")


# ==============================================================================
# DATA OUTPUT - Display full data array
# ==============================================================================

print("\nFull data array:")
print(data_ch_V)


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nCleaning up...")

# Release Red Pitaya resources
rp.rp_Release()

print("Resources released - program complete")
print("\nNote: Captured data is displayed above")
print("      For further analysis, save data_ch_V array to file or plot it")
