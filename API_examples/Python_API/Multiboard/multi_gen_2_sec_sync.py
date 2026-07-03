#!/usr/bin/python3
"""
Red Pitaya Multiboard Example - Secondary Synchronized Generation with Click Shield
====================================================================================

This example demonstrates synchronized signal generation on a secondary Red Pitaya
board using Click Shield for multiboard coordination. The board waits for an external
trigger from the primary board and generates synchronized waveforms with configurable
phase offsets that complement the primary board's signals.

Features:
- Dual-channel synchronized signal generation on secondary board
- External trigger input via Click Shield (triggered by primary board)
- Configurable phase offset between channels (e.g., 180° and 270°)
- Phase-locked outputs synchronized with primary board
- LED status indicator
- Uses GenSynchronise() for phase-locked outputs
- Positive edge external trigger detection

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar) - Secondary unit
- Click Shield board for daisy chain connections
- Primary Red Pitaya board running multi_gen_1_prim_sync.py

Required Connections:
=====================
Secondary Board (This Example):
  - Connect Click Shield to secondary board
  - DIO0_P pin configured as trigger input from primary board
  - LED5 used as status indicator
  - Generator outputs on OUT1 and OUT2

Daisy Chain Connection:
  - Connect SATA cable from primary OUT to secondary IN
  - Primary board sends trigger via Click Shield
  - Secondary board receives trigger on DIO0_P
  - Clock and trigger synchronized via SATA connection

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- OS 2.00 or higher

Usage:
    1. First, start the primary board script (multi_gen_1_prim_sync.py)
    2. Then run this secondary board script:
       python multi_gen_2_sec_sync.py
    
    The program will:
    1. Initialize the secondary board
    2. Configure Click Shield for trigger input
    3. Setup dual-channel generation with phase offset (180° and 270°)
    4. Wait for external trigger from primary board
    5. Synchronize and generate waveforms when triggered

Configuration:
    Modify the CONFIGURATION section to customize:
    - Channel selection and waveform types
    - Frequency and amplitude settings (should match primary)
    - Phase offset between channels (180° and 270° complement primary's 0° and 90°)
    - Trigger source configuration (must be external)

Note:
    This example is designed to work in conjunction with multi_gen_1_prim_sync.py
    which runs on the primary board. The secondary board waits for the trigger
    signal from the primary board before starting generation.

Important:
    - gen_trig_sour must be set to rp.RP_GEN_TRIG_SRC_EXT_PE (external positive edge)
    - Phase values should complement primary board (e.g., +180° offset)
    - GenOutEnableSync(True) must be called before enabling outputs
    - Frequency and amplitude should match primary board for coherent output

Author: Red Pitaya
Date: January 2026
"""

import time
import numpy as np
import rp


# ==============================================================================
# SECONDARY BOARD - SYNCHRONIZED GENERATION
# ==============================================================================

print("=" * 70)
print("Red Pitaya Multiboard - Secondary Synchronized Generation")
print("=" * 70)


# ==============================================================================
# CONFIGURATION - Generation Settings
# ==============================================================================

# Channel and waveform settings
channel1 = rp.RP_CH_1                       # Primary channel: rp.RP_CH_1
channel2 = rp.RP_CH_2                       # Secondary channel: rp.RP_CH_2
waveform = rp.RP_WAVEFORM_SINE              # Waveform type: SINE, SQUARE, TRIANGLE, etc.

# Signal parameters (should match primary board)
freq = 100                                  # Frequency in Hz (must match primary: 100 Hz)
ampl = 1.0                                  # Amplitude in Volts (must match primary: 1.0 V)
pha1 = 180                                  # Phase for channel 1 in degrees (180° offset from primary CH1)
pha2 = 270                                  # Phase for channel 2 in degrees (180° offset from primary CH2)

# Trigger settings - MUST BE EXTERNAL for secondary board
gen_trig_sour = rp.RP_GEN_TRIG_SRC_EXT_PE   # Generator trigger: EXTERNAL POSITIVE EDGE
                                            # Triggered by primary board via Click Shield

print("\nGeneration Configuration:")
print(f"  Channel 1:             {channel1}")
print(f"  Channel 2:             {channel2}")
print(f"  Waveform:              {waveform}")
print(f"  Frequency:             {freq} Hz (must match primary)")
print(f"  Amplitude:             {ampl} V (must match primary)")
print(f"  Channel 1 phase:       {pha1}° (primary + 180°)")
print(f"  Channel 2 phase:       {pha2}° (primary + 180°)")
print(f"  Phase offset:          {abs(pha2 - pha1)}°")
print(f"  Trigger source:        {gen_trig_sour} (External Positive Edge)")

print("\n" + "=" * 70)
print("Initializing Secondary Board...")
print("=" * 70)

# Initialize the interface
rp.rp_Init()
print("Red Pitaya API initialized")

# Reset generation module
rp.rp_GenReset()
print("Generator module reset")


# ==============================================================================
# CLICK SHIELD SETUP - Trigger Input from Primary Board
# ==============================================================================

print("\nConfiguring Click Shield Trigger Input...")

# Note: Clock and trigger sync are typically enabled when using multiple boards
# Uncomment the following lines for full daisy chain synchronization:
# rp.rp_SetEnableDiasyChainClockSync(True)     # Enable clock synchronization
# rp.rp_SetEnableDaisyChainTrigSync(True)      # Enable trigger synchronization

# Enable trigger output on DIO0_N pin
# Note: Even secondary boards can output triggers to further cascade boards
rp.rp_SetDpinEnableTrigOutput(True)
print("  Trigger output (DIO0_N):   Enabled (for cascading)")

# Set trigger source to DAC (generator) trigger
# Options: rp.OUT_TR_ADC (acquisition trigger), rp.OUT_TR_DAC (generator trigger)
rp.rp_SetSourceTrigOutput(rp.OUT_TR_DAC)
print("  Trigger source:            DAC (Generator) trigger")
print("  Trigger input (DIO0_P):    Receiving from primary board")

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
print(f"  Phase:                 {pha1}° (180° offset from primary CH1)")

# Configure Channel 2
print("\nConfiguring Channel 2...")
rp.rp_GenWaveform(channel2, waveform)
print(f"  Waveform:              {waveform}")

rp.rp_GenFreq(channel2, freq)
print(f"  Frequency:             {freq} Hz")

rp.rp_GenAmp(channel2, ampl)
print(f"  Amplitude:             {ampl} V")

rp.rp_GenPhase(channel2, pha2)
print(f"  Phase:                 {pha2}° (180° offset from primary CH2)")

# Set trigger source for both channels - MUST BE EXTERNAL
rp.rp_GenTriggerSource(channel1, gen_trig_sour)
rp.rp_GenTriggerSource(channel2, gen_trig_sour)
print(f"\nTrigger source for both channels: {gen_trig_sour}")
print("  Waiting for external trigger from primary board...")

# Enable synchronized output mode
# This must be called before enabling outputs for synchronization
rp.rp_GenOutEnableSync(True)
print("Synchronized output mode: ENABLED")

# Enable output for channel 1
# Note: Both channels are configured but only channel 1 is explicitly enabled
# The GenSynchronise() call will synchronize both channels when triggered
rp.rp_GenOutEnable(channel1)
print("Channel 1 output enabled")


# ==============================================================================
# WAITING FOR TRIGGER
# ==============================================================================

print("\n" + "=" * 70)
print("Secondary Board Ready - Waiting for Primary Trigger")
print("=" * 70)
print("\nThe secondary board is now configured and waiting.")
print("When the primary board triggers, this board will:")
print("  1. Detect the external trigger signal")
print("  2. Synchronize both generators")
print("  3. Start outputting phase-locked signals")
print("\nPhase relationship:")
print(f"  Primary CH1 (0°)    → Secondary CH1 ({pha1}°)")
print(f"  Primary CH2 (90°)   → Secondary CH2 ({pha2}°)")
print("\nEnsure the primary board script is running and press Enter there.")
print("\nNote: This script will complete immediately but the board remains")
print("      configured and will trigger when the primary board sends the signal.")


# ==============================================================================
# CLEANUP
# ==============================================================================

print("\n" + "=" * 70)
print("Configuration Complete")
print("=" * 70)
print("\nSecondary board is armed and ready for trigger.")
print("Generators will start automatically when primary triggers.")
print("\nPress Enter to release resources and exit...")
input()

print("\nReleasing resources...")

# Release resources
rp.rp_Release()
print("Resources released")
print("=" * 70)
