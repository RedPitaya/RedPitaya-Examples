#!/usr/bin/python3
"""
Red Pitaya Split Trigger Acquisition Example
=============================================

This example demonstrates split trigger mode acquisition on Red Pitaya, allowing
independent trigger configuration for each input channel. Each channel can have
its own trigger source and trigger level, enabling simultaneous multi-channel
acquisition with different trigger conditions.

Split trigger mode is useful for:
- Capturing events on multiple channels with different trigger conditions
- Multi-channel monitoring with independent triggering
- Complex measurement setups requiring channel-specific triggers

Features:
- Independent trigger configuration per channel
- Supports 2-channel or 4-channel (STEMlab 125-14 4-Input) boards
- Configurable decimation per channel
- Timeout protection for trigger waiting
- Random acquisition order to demonstrate independence

Hardware Requirements:
- Red Pitaya board:
  * Any Red Pitaya board (2 channels: CH1, CH2)
  * STEMlab 125-14 4-Input (4 channels: CH1, CH2, CH3, CH4)
- Signal sources connected to input channels for triggering

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- OS 2.00 or higher (for split trigger mode support)

Usage:
    python acq_4_split_trigger.py
    
    Set ch_num to 2 or 4 depending on your board model.
    Configure trigger sources for each channel.
    The program will acquire data from all channels independently.

Configuration:
    Modify parameters in the CONFIGURATION section:
    - ch_num: Number of channels (2 or 4)
    - dec: Decimation factors for each channel
    - triggers: Trigger source for each channel
    - trig_lvl: Trigger level in volts
    - buff_size: Number of samples to capture per channel

Author: Red Pitaya
Date: January 2026
"""

import time
import numpy as np
import rp


# ==============================================================================
# CONFIGURATION - Set your split trigger acquisition parameters
# ==============================================================================

# Board configuration
# Set up to 2 for any Red Pitaya board (2-channel)
# Set up to 4 for STEMlab 125-14 4-Input (4-channel)
ch_num = 2                      # Number of channels to acquire

# Channel definitions
channels = [rp.RP_CH_1, rp.RP_CH_2, rp.RP_CH_3, rp.RP_CH_4]

# Decimation factors for each channel
# Available decimations: 1, 2, 4, 8, 16, 17, 18, ..., 65536
#   Decimation 1 = 125 MS/s
#   Decimation 8 = 15.625 MS/s
#   Sample rate = 125 MS/s / decimation
dec = [1, 1, 1, 1]              # Decimation for CH1, CH2, CH3, CH4

# Trigger configuration for each channel
# Available trigger sources per channel:
#   RP_TRIG_SRC_DISABLED - No trigger
#   RP_TRIG_SRC_NOW - Immediate trigger
#   RP_TRIG_SRC_CHA_PE - Channel A positive edge
#   RP_TRIG_SRC_CHA_NE - Channel A negative edge
#   RP_TRIG_SRC_CHB_PE - Channel B positive edge
#   RP_TRIG_SRC_CHB_NE - Channel B negative edge
#   RP_TRIG_SRC_CHC_PE - Channel C positive edge (4-Input only)
#   RP_TRIG_SRC_CHC_NE - Channel C negative edge (4-Input only)
#   RP_TRIG_SRC_CHD_PE - Channel D positive edge (4-Input only)
#   RP_TRIG_SRC_CHD_NE - Channel D negative edge (4-Input only)
#   RP_TRIG_SRC_EXT_PE - External trigger positive edge
#   RP_TRIG_SRC_EXT_NE - External trigger negative edge
#   RP_TRIG_SRC_AWG_PE - Generator positive edge
#   RP_TRIG_SRC_AWG_NE - Generator negative edge
triggers = [rp.RP_TRIG_SRC_CHA_PE, rp.RP_TRIG_SRC_CHB_PE, 
            rp.RP_TRIG_SRC_CHC_NE, rp.RP_TRIG_SRC_CHD_NE]

trig_lvl = 0.1                  # Trigger level in volts (applied to all channels)
buff_size = 6000                # Number of samples to capture per channel
timeout_seconds = 10            # Timeout in seconds for trigger waiting

print("=" * 70)
print("Red Pitaya Split Trigger Acquisition Configuration")
print("=" * 70)
print(f"Board model:         {'STEMlab 125-14 4-Input (4 channels)' if (4 >= ch_num > 2) else 'Red Pitaya (2 channels)'}")
print(f"Active channels:     {ch_num}")
print(f"Samples per channel: {buff_size}")
print(f"Trigger level:       {trig_lvl} V")
print(f"Timeout:             {timeout_seconds} seconds")
print()
print("Channel configuration:")
for i in range(ch_num):
    sample_rate = 125000000 / dec[i] / 1000000
    print(f"  CH{i+1}: Decimation={dec[i]} ({sample_rate:.2f} MS/s), Trigger={triggers[i]}")
print()
print("NOTE: Split trigger mode allows independent triggering per channel")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya
# ==============================================================================

print("\nInitializing Red Pitaya...")

# Initialize the Red Pitaya interface
result = rp.rp_Init()
if result != rp.RP_OK:
    print(f"ERROR: Initialization failed with code {result}")
    exit(1)
print("Red Pitaya initialized")


# ==============================================================================
# SPLIT TRIGGER MODE ACTIVATION - Enable split trigger mode
# ==============================================================================

print("\nActivating split trigger mode...")

# Activate split trigger mode (allows independent triggers per channel)
result = rp.rp_AcqSetSplitTrigger(True)
if result != rp.RP_OK:
    print(f"ERROR: Failed to activate split trigger mode with code {result}")
    exit(1)

# Verify split trigger mode is active
split_trig_state = rp.rp_AcqGetSplitTrigger()[1]
print(f"Split trigger mode: {'ENABLED' if split_trig_state else 'DISABLED'}")

if not split_trig_state:
    print("ERROR: Split trigger mode activation failed")
    exit(1)


# ==============================================================================
# CHANNEL RESET AND CONFIGURATION - Configure each channel
# ==============================================================================

print("\nConfiguring channels...")

# Reset each channel
for i in range(ch_num):
    result = rp.rp_AcqResetCh(channels[i])
    if result == rp.RP_OK:
        print(f"  CH{i+1} reset successful")
    else:
        print(f"  WARNING: CH{i+1} reset returned code {result}")

# Configure decimation and trigger level for each channel
print("\nSetting channel parameters...")
for i in range(ch_num):
    # Set decimation
    result = rp.rp_AcqSetDecimationFactorCh(channels[i], dec[i])
    if result == rp.RP_OK:
        print(f"  CH{i+1}: Decimation set to {dec[i]}")
    else:
        print(f"  ERROR: CH{i+1} decimation setting failed with code {result}")
    
    # Set trigger level
    result = rp.rp_AcqSetTriggerLevel(channels[i], trig_lvl)
    if result == rp.RP_OK:
        print(f"  CH{i+1}: Trigger level set to {trig_lvl} V")
    else:
        print(f"  ERROR: CH{i+1} trigger level setting failed with code {result}")


# ==============================================================================
# ACQUISITION START - Start acquisition on each channel
# ==============================================================================

print("\nStarting acquisition on all channels...")

for i in range(ch_num):
    result = rp.rp_AcqStartCh(channels[i])
    if result == rp.RP_OK:
        print(f"  CH{i+1}: Acquisition started")
    else:
        print(f"  ERROR: CH{i+1} acquisition start failed with code {result}")


# ==============================================================================
# TRIGGER CONFIGURATION - Set trigger sources for each channel
# ==============================================================================

print("\nConfiguring trigger sources...")

for i in range(ch_num):
    result = rp.rp_AcqSetTriggerSrcCh(channels[i], triggers[i])
    if result == rp.RP_OK:
        print(f"  CH{i+1}: Trigger source set to {triggers[i]}")
    else:
        print(f"  ERROR: CH{i+1} trigger source setting failed with code {result}")

print("\nAcquisition configured and armed")
print("Waiting for trigger events on each channel...")


# ==============================================================================
# TRIGGER WAITING - Wait for triggers in random order
# ==============================================================================

# Generate random acquisition order to demonstrate channel independence
trig_ord = np.array(np.arange(1, ch_num + 1))
np.random.shuffle(trig_ord)
print(f"\nMonitoring channels in random order: {trig_ord}")

# Wait for trigger on each channel
timeout_reached = False

print("\nWaiting for trigger events...")
for i in trig_ord:
    start_time = time.time()
    ch_idx = i - 1  # Convert to 0-based index
    
    print(f"  Waiting for CH{i} trigger...")
    
    while True:
        trig_state = rp.rp_AcqGetTriggerStateCh(channels[ch_idx])[1]
        if trig_state == rp.RP_TRIG_STATE_TRIGGERED:
            print(f"  CH{i}: Trigger detected!")
            break
        
        if time.time() - start_time > timeout_seconds:
            print(f"  CH{i}: TIMEOUT - No trigger received")
            timeout_reached = True
            break

# Wait for buffer fill on each channel
print("\nWaiting for buffers to fill...")
for i in trig_ord:
    start_time = time.time()
    ch_idx = i - 1  # Convert to 0-based index
    
    print(f"  Waiting for CH{i} buffer fill...")
    
    while True:
        if rp.rp_AcqGetBufferFillStateCh(channels[ch_idx])[1]:
            print(f"  CH{i}: Buffer filled!")
            break
        
        if time.time() - start_time > timeout_seconds:
            print(f"  CH{i}: TIMEOUT - Buffer fill timeout")
            timeout_reached = True
            break

# Stop acquisition on all channels
print("\nStopping acquisition...")
for i in range(ch_num):
    rp.rp_AcqStopCh(channels[i])
    print(f"  CH{i+1}: Stopped")

print("All buffers filled" if not timeout_reached else "Acquisition completed with timeouts")


# ==============================================================================
# DATA RETRIEVAL - Read captured data from all channels
# ==============================================================================

print("\nRetrieving captured data...")

buffers = []
trigger_pos = [0] * ch_num

if not timeout_reached:
    # Preallocate buffer for all channels
    buffers = np.empty((ch_num, buff_size), dtype=np.float32)
    
    for i in range(ch_num):
        # Get trigger position for each channel
        trigger_pos[i] = rp.rp_AcqGetWritePointerCh(channels[i])[1]
        
        # Retrieve samples after trigger using NumPy-based function
        result = rp.rp_AcqGetDataVNP(channels[i], trigger_pos[i], buffers[i])
        
        if result == rp.RP_OK:
            print(f"  CH{i+1}: Retrieved {buff_size} samples (trigger pos: {trigger_pos[i]})")
        else:
            print(f"  ERROR: CH{i+1} data retrieval failed with code {result}")
    
    # Display statistics for each channel
    print("\nData statistics:")
    for i in range(ch_num):
        print(f"  CH{i+1}: Range={buffers[i].min():.6f}V to {buffers[i].max():.6f}V, Mean={buffers[i].mean():.6f}V")
    
    # Display first 10 samples from each channel
    print("\nFirst 10 samples from each channel:")
    for i in range(ch_num):
        print(f"\n  CH{i+1}:")
        for j in range(min(10, buff_size)):
            print(f"    Sample [{j}]: {buffers[i][j]:.6f} V")

else:
    print("ERROR: Data acquisition failed due to timeout")
    print("       Check that signals are connected and trigger conditions are met")


# ==============================================================================
# DATA OUTPUT - Display full data arrays
# ==============================================================================

if not timeout_reached and len(buffers) > 0:
    print("\nFull data arrays:")
    for i in range(ch_num):
        print(f"\nCH{i+1} data in volts:")
        print(buffers[i])


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nCleaning up...")

# Release Red Pitaya resources
rp.rp_Release()

print("Resources released - program complete")
print("\nNote: Captured data is displayed above")
print("      For further analysis, save buffers array to file or plot it")
