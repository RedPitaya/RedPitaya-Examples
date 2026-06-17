#!/usr/bin/python3
"""
Red Pitaya Interrupt-Based Acquisition and Generation Example
=============================================================

This example demonstrates interrupt-driven data acquisition with synchronized
signal generation on Red Pitaya. Instead of polling trigger and buffer fill
states, it uses hardware interrupts to wait for trigger and buffer fill events,
which is more efficient for time-sensitive applications.

Features:
- Synchronized dual-channel signal generation (OUT1 and OUT2)
- Interrupt-based trigger detection (more efficient than polling)
- Interrupt-based buffer fill detection
- Configurable interrupt masks for trigger and fill events
- Data output in both raw ADC values and calibrated volts
- Configurable trigger level and delay

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Connect OUT1 to IN1 for loopback testing

Software Requirements:
- Red Pitaya Python API (rp module)
- rp_overlay module (for FPGA overlay)
- NumPy library
- OS 2.00 or higher

Usage:
    python acq_gen_2_interrupt_trig.py

    For loopback testing: Connect OUT1 to IN1 with a cable or jumper.
    The program generates a signal and captures it using interrupt-driven
    acquisition.

Configuration:
    Modify parameters in the CONFIGURATION section:
    - waveform: Signal type (sine, square, triangle, etc.)
    - freq: Signal frequency in Hz
    - ampl: Signal amplitude in volts
    - dec: Decimation factor (affects sample rate)
    - trig_lvl: Trigger threshold voltage
    - N: Number of samples to capture

Author: Red Pitaya
Date: May 2026
"""

import time
import numpy as np
from rp_overlay import overlay
import rp


# ==============================================================================
# CONFIGURATION - Set your acquisition and generation parameters
# ==============================================================================

# Generation parameters
channel = rp.RP_CH_1            # Primary output channel
channel2 = rp.RP_CH_2          # Secondary output channel

# Waveform type
# Available waveforms:
#   RP_WAVEFORM_SINE, RP_WAVEFORM_SQUARE, RP_WAVEFORM_TRIANGLE,
#   RP_WAVEFORM_RAMP_UP, RP_WAVEFORM_RAMP_DOWN, RP_WAVEFORM_DC,
#   RP_WAVEFORM_PWM, RP_WAVEFORM_ARBITRARY, RP_WAVEFORM_DC_NEG,
#   RP_WAVEFORM_SWEEP
waveform = rp.RP_WAVEFORM_SINE

freq = 100000                   # Frequency in Hz (100 kHz)
ampl = 1.0                      # Amplitude in volts

# Acquisition parameters
# Available decimations: 1, 2, 4, 8, 16, 17, 18, ..., 65536
#   Decimation 1   = 125 MS/s
#   Decimation 8   = 15.625 MS/s
#   Sample rate    = 125 MS/s / decimation
dec = rp.RP_DEC_1               # Decimation factor

N = 128                         # Number of samples to capture

# Trigger parameters
# Available acquisition trigger sources:
#   RP_TRIG_SRC_DISABLED - No trigger
#   RP_TRIG_SRC_NOW      - Immediate trigger
#   RP_TRIG_SRC_CHA_PE   - Channel A positive edge
#   RP_TRIG_SRC_CHA_NE   - Channel A negative edge
#   RP_TRIG_SRC_CHB_PE   - Channel B positive edge
#   RP_TRIG_SRC_CHB_NE   - Channel B negative edge
#   RP_TRIG_SRC_EXT_PE   - External trigger positive edge
#   RP_TRIG_SRC_EXT_NE   - External trigger negative edge
#   RP_TRIG_SRC_AWG_PE   - Generator positive edge
#   RP_TRIG_SRC_AWG_NE   - Generator negative edge
acq_trig_sour = rp.RP_TRIG_SRC_CHA_PE

trig_lvl = 0.125                # Trigger threshold in volts
trig_dly = 0                    # Trigger delay in samples

# Interrupt timeout in milliseconds
trig_timeout_ms = 1000          # Timeout for trigger interrupt
fill_timeout_ms = 1000          # Timeout for buffer fill interrupt

print("=" * 70)
print("Red Pitaya Interrupt-Based Acquisition and Generation Configuration")
print("=" * 70)
print(f"Generator channel 1: {channel}")
print(f"Generator channel 2: {channel2}")
print(f"Waveform:            {waveform}")
print(f"Frequency:           {freq} Hz")
print(f"Amplitude:           {ampl} V")
print()
print(f"Decimation:          {dec}")
print(f"Samples to capture:  {N}")
print(f"Trigger source:      {acq_trig_sour}")
print(f"Trigger level:       {trig_lvl} V")
print(f"Trigger delay:       {trig_dly} samples")
print(f"Trigger timeout:     {trig_timeout_ms} ms")
print(f"Fill timeout:        {fill_timeout_ms} ms")
print("NOTE: Connect OUT1 to IN1 for loopback testing")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize FPGA overlay and Red Pitaya API
# ==============================================================================

print("\nInitializing FPGA overlay and Red Pitaya...")

fpga = overlay()

# Uncomment to enable debug registers if needed
# rp.rp_EnableDebugReg()

rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# RESET - Reset generation and acquisition
# ==============================================================================

print("\nResetting generator and acquisition...")

rp.rp_GenReset()
rp.rp_AcqReset()
print("Generator and acquisition reset to default state")


# ==============================================================================
# GENERATION SETUP - Configure signal generation
# ==============================================================================

print("\nConfiguring signal generation...")

# Configure OUT1
rp.rp_GenWaveform(channel, waveform)
rp.rp_GenFreqDirect(channel, freq)
rp.rp_GenAmp(channel, ampl)
print(f"OUT1 configured: {waveform}, {freq} Hz, {ampl} V")

# Configure OUT2
rp.rp_GenWaveform(channel2, waveform)
rp.rp_GenFreqDirect(channel2, freq)
rp.rp_GenAmp(channel2, ampl)
print(f"OUT2 configured: {waveform}, {freq} Hz, {ampl} V")

# Enable output synchronization
rp.rp_GenOutEnableSync(True)
print("Generator output synchronization enabled")


# ==============================================================================
# ACQUISITION SETUP - Configure data acquisition with interrupts
# ==============================================================================

print("\nConfiguring data acquisition with interrupt support...")

# Set decimation factor
rp.rp_AcqSetDecimation(dec)
print(f"Decimation set to: {dec}")

# Set trigger level and delay
rp.rp_AcqSetTriggerLevel(rp.RP_T_CH_1, trig_lvl)
rp.rp_AcqSetTriggerDelay(trig_dly)
print(f"Trigger configured: Level = {trig_lvl} V, Delay = {trig_dly} samples")

# Configure interrupt masks
# False = interrupt enabled, True = interrupt masked (disabled)
rp.rp_AcqSetIntMask(rp.RP_INT_TRIGGER, False)   # Enable trigger interrupt
# rp.rp_AcqSetIntMask(rp.RP_INT_FILL, False)    # Optionally enable fill interrupt
print(f"Trigger interrupt mask: {rp.rp_AcqGetIntMask(rp.RP_INT_TRIGGER)[1]}")
print(f"Fill interrupt mask:    {rp.rp_AcqGetIntMask(rp.RP_INT_FILL)[1]}")


# ==============================================================================
# TRIGGER AND CAPTURE - Start acquisition and wait for interrupt events
# ==============================================================================

print("\nStarting acquisition...")
rp.rp_AcqStart()
time.sleep(0.1)

# Set acquisition trigger source
rp.rp_AcqSetTriggerSrc(acq_trig_sour)
print(f"Acquisition trigger source set to: {acq_trig_sour}")
time.sleep(0.1)

# Trigger the generator to produce the signal
print("Triggering generator...")
rp.rp_GenTriggerOnly(channel)
print("Generator triggered")

# Wait for trigger interrupt
print(f"Waiting for trigger interrupt (timeout: {trig_timeout_ms} ms)...")
ret = rp.rp_AcqIntTriggerRead(trig_timeout_ms)
print(f"Trigger IRQ result: {rp.rp_GetError(ret)}")

# Wait for buffer fill interrupt
print(f"Waiting for buffer fill interrupt (timeout: {fill_timeout_ms} ms)...")
ret = rp.rp_AcqIntFillRead(fill_timeout_ms)
print(f"Fill IRQ result: {rp.rp_GetError(ret)}")


# ==============================================================================
# DATA RETRIEVAL - Read captured data
# ==============================================================================

print("\nRetrieving captured data...")

# Get trigger write pointer position
trig_pos = rp.rp_AcqGetWritePointerAtTrig()[1]
print(f"Trigger write pointer position: {trig_pos}")

# Allocate buffers for raw and voltage data
arr_i16 = np.zeros(N, dtype=np.int16)
arr_f = np.zeros(N, dtype=np.float32)

# Get raw ADC data with calibration
res = rp.rp_AcqGetDataRawWithCalibNP(rp.RP_CH_1, trig_pos, arr_i16)
print(f"Retrieved {N} raw samples from CH1")

# Get voltage data
res = rp.rp_AcqGetDataVNP(rp.RP_CH_1, trig_pos, arr_f)
print(f"Retrieved {N} voltage samples from CH1")
print(f"Voltage range: {arr_f.min():.6f} V to {arr_f.max():.6f} V")
print(f"Raw ADC range: {arr_i16.min()} to {arr_i16.max()}")


# ==============================================================================
# DATA OUTPUT - Display captured data
# ==============================================================================

print("\nCaptured data:")
print(f"\nRaw ADC values (with calibration):\n{arr_i16}")
print(f"\nData in Volts:\n{arr_f}")


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nCleaning up...")

rp.rp_Release()

print("Resources released - program complete")
print("\nNote: Captured data is displayed above")
print("      For further analysis, save arrays to file or plot them")