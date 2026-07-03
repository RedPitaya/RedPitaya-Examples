#!/usr/bin/python3
"""
Red Pitaya Multiboard Example - Primary Synchronized Generation with Click Shield
==================================================================================

This example demonstrates synchronized signal generation on a primary Red Pitaya
board using Click Shield for multiboard coordination. The board generates synchronized
waveforms on two channels with configurable phase offsets and can trigger secondary
boards via the Click Shield daisy chain connection.

Features:
- Dual-channel synchronized signal generation on primary board
- Configurable phase offset between channels (e.g., 0° and 90° for quadrature)
- Click Shield trigger output to synchronize secondary boards
- Manual trigger control for precise timing
- LED status indicator
- Uses GenSynchronise() for phase-locked outputs
- Support for internal trigger source

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar) - Primary unit
- Click Shield board for daisy chain connections
- Optional: Secondary Red Pitaya boards for multi-channel setup

Required Connections:
=====================
Primary Board (This Example):
  - Connect Click Shield to primary board
  - DIO0_N pin configured as trigger output
  - LED5 used as status indicator
  - Generator outputs on OUT1 and OUT2

For Multi-board Setup:
  - Connect SATA cable from primary OUT to secondary IN
  - Trigger synchronization via Click Shield
  - DAC trigger output enabled for generator synchronization

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- OS 2.00 or higher

Usage:
    python multi_gen_1_prim_sync.py
    
    The program will:
    1. Initialize the primary board
    2. Configure Click Shield trigger output
    3. Setup dual-channel generation with phase offset
    4. Wait for user input (Press Enter)
    5. Synchronize and start both generators
    6. Output synchronized waveforms

Configuration:
    Modify the CONFIGURATION section to customize:
    - Channel selection and waveform types
    - Frequency and amplitude settings
    - Phase offset between channels
    - Trigger source configuration

Note:
    This example focuses on the primary board generator synchronization.
    For complete multiboard setup, use this in conjunction with secondary
    board examples that listen for external triggers.

Important:
    - GenOutEnableSync(True) must be called before enabling outputs
    - rp_GenSynchronise() triggers both generators simultaneously
    - Phase alignment ensures precise channel relationships
    - Use rp_GenTriggerOnlyBoth() for re-triggering without reset

Author: Red Pitaya
Date: January 2026
"""

import time
import numpy as np
import rp


# ==============================================================================
# PRIMARY BOARD - SYNCHRONIZED GENERATION
# ==============================================================================

print("=" * 70)
print("Red Pitaya Multiboard - Primary Synchronized Generation")
print("=" * 70)


# ==============================================================================
# CONFIGURATION - Generation Settings
# ==============================================================================

# Channel and waveform settings
channel1 = rp.RP_CH_1                       # Primary channel: rp.RP_CH_1
channel2 = rp.RP_CH_2                       # Secondary channel: rp.RP_CH_2
waveform = rp.RP_WAVEFORM_SINE              # Waveform type: SINE, SQUARE, TRIANGLE, etc.

# Signal parameters
freq = 100                                  # Frequency in Hz (100 Hz)
ampl = 1.0                                  # Amplitude in Volts (peak)
pha1 = 0                                    # Phase for channel 1 in degrees
pha2 = 90                                   # Phase for channel 2 in degrees (quadrature)

# Trigger settings
gen_trig_sour = rp.RP_GEN_TRIG_SRC_INTERNAL # Generator trigger: INTERNAL, EXT_PE, EXT_NE

print("\nGeneration Configuration:")
print(f"  Channel 1:             {channel1}")
print(f"  Channel 2:             {channel2}")
print(f"  Waveform:              {waveform}")
print(f"  Frequency:             {freq} Hz")
print(f"  Amplitude:             {ampl} V")
print(f"  Channel 1 phase:       {pha1}°")
print(f"  Channel 2 phase:       {pha2}°")
print(f"  Phase offset:          {abs(pha2 - pha1)}°")
print(f"  Trigger source:        {gen_trig_sour}")


# ==============================================================================
# INITIALIZATION - Primary Board
# ==============================================================================

print("\n" + "=" * 70)
print("Initializing Primary Board...")
print("=" * 70)

# Initialize the interface
rp.rp_Init()
print("Red Pitaya API initialized")

# Reset generation module
rp.rp_GenReset()
print("Generator module reset")


# ==============================================================================
# CLICK SHIELD SETUP - Trigger Output for Multiboard
# ==============================================================================

print("\nConfiguring Click Shield Trigger Output...")

# Note: Clock and trigger sync are typically enabled when using secondary boards
# Uncomment the following lines when connecting to secondary boards:
# rp.rp_SetEnableDiasyChainClockSync(True)     # Enable clock synchronization
# rp.rp_SetEnableDaisyChainTrigSync(True)      # Enable trigger synchronization

# Enable trigger output on DIO0_N pin
rp.rp_SetDpinEnableTrigOutput(True)
print("  Trigger output (DIO0_N):   Enabled")

# Set trigger source to DAC (generator) trigger
# This sends generator trigger to secondary boards
# Options: rp.OUT_TR_ADC (acquisition trigger), rp.OUT_TR_DAC (generator trigger)
rp.rp_SetSourceTrigOutput(rp.OUT_TR_DAC)
print("  Trigger source:            DAC (Generator) trigger")

# Turn on LED5 as visual indicator
rp.rp_DpinSetState(rp.RP_LED5, rp.RP_HIGH)
print("  Status LED (LED5):         ON")


# ==============================================================================
# SIGNAL GENERATION - Dual Channel Synchronized Setup
# ==============================================================================

print("\n" + "=" * 70)
print("Configuring Synchronized Dual-Channel Generation...")
print("=" * 70)

# Configure Channel 1
print("\nConfiguring Channel 1...")
rp.rp_GenWaveform(channel1, waveform)
print(f"  Waveform:              {waveform}")

rp.rp_GenFreq(channel1, freq)
print(f"  Frequency:             {freq} Hz")

rp.rp_GenAmp(channel1, ampl)
print(f"  Amplitude:             {ampl} V")

rp.rp_GenPhase(channel1, pha1)
print(f"  Phase:                 {pha1}°")

# Configure Channel 2
print("\nConfiguring Channel 2...")
rp.rp_GenWaveform(channel2, waveform)
print(f"  Waveform:              {waveform}")

rp.rp_GenFreq(channel2, freq)
print(f"  Frequency:             {freq} Hz")

rp.rp_GenAmp(channel2, ampl)
print(f"  Amplitude:             {ampl} V")

rp.rp_GenPhase(channel2, pha2)
print(f"  Phase:                 {pha2}°")

# Set trigger source for both channels
rp.rp_GenTriggerSource(channel1, gen_trig_sour)
rp.rp_GenTriggerSource(channel2, gen_trig_sour)
print(f"\nTrigger source for both channels: {gen_trig_sour}")

# Enable synchronized output mode
# This must be called before enabling outputs for synchronization
rp.rp_GenOutEnableSync(True)
print("Synchronized output mode: ENABLED")

# Enable output for channel 1
# Note: Both channels are configured but only channel 1 is explicitly enabled
# The GenSynchronise() call will synchronize both channels
rp.rp_GenOutEnable(channel1)
print("Channel 1 output enabled")


# ==============================================================================
# SYNCHRONIZATION AND TRIGGERING
# ==============================================================================

print("\n" + "=" * 70)
print("Ready to Start Synchronized Generation")
print("=" * 70)
print("\nBoth channels are configured and ready.")
print("Press Enter to synchronize and start generation...")
input()

# Synchronize and start both generators
# This triggers both channels simultaneously with phase alignment
rp.rp_GenSynchronise()
print("\nGenerators synchronized and started!")
print("Both channels are now outputting phase-locked signals.")

# Note: Use rp_GenTriggerOnlyBoth() to re-trigger without resetting waveform position
print("\nTip: Use rp.rp_GenTriggerOnlyBoth() to re-trigger without phase reset")


# ==============================================================================
# CLEANUP
# ==============================================================================

print("\n" + "=" * 70)
print("Generation Complete")
print("=" * 70)
print("\nSynchronized signals are being generated.")
print("Press Ctrl+C to stop and release resources.")

try:
    # Keep program running to maintain signal generation
    input("\nPress Enter to stop generation and exit...")
except KeyboardInterrupt:
    print("\n\nInterrupted by user")

print("\nReleasing resources...")

# Release resources
rp.rp_Release()
print("Resources released")
print("=" * 70)
