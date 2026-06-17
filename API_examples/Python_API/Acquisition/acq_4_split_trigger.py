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
- Round-robin polling so no channel's buffer is missed while waiting on another
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

    Configure trigger sources for each channel in the CONFIGURATION section.
    The program will acquire data from all channels independently.

Configuration:
    Modify parameters in the CONFIGURATION section:
    - dec: Decimation factors for each channel (index 0 = CH1, etc.)
    - trig_src: Trigger source per channel
    - trig_lvl: Trigger level in volts per channel
    - trig_dly: Trigger delay in samples per channel
    - buff_size: Number of samples to capture per channel

Author: Red Pitaya
Date: May 2026
"""

import time
import numpy as np
import rp
import rp_hw_profiles


# ==============================================================================
# CONFIGURATION - Set your split trigger acquisition parameters
# ==============================================================================

# Decimation factors for each channel (index 0 = CH1, 1 = CH2, ...)
# Available decimations: 1, 2, 4, 8, 16, 17, 18, ..., 65536
#   Decimation 1 = 125 MS/s
#   Decimation 8 = 15.625 MS/s
#   Sample rate  = 125 MS/s / decimation
dec = [1, 1, 1, 1]                     # Decimation for CH1, CH2, CH3, CH4

# Trigger source for each channel
# Available trigger sources:
#   RP_TRIG_SRC_DISABLED - No trigger
#   RP_TRIG_SRC_NOW      - Immediate trigger
#   RP_TRIG_SRC_CHA_PE   - Channel A positive edge
#   RP_TRIG_SRC_CHA_NE   - Channel A negative edge
#   RP_TRIG_SRC_CHB_PE   - Channel B positive edge
#   RP_TRIG_SRC_CHB_NE   - Channel B negative edge
#   RP_TRIG_SRC_CHC_PE   - Channel C positive edge (4-Input only)
#   RP_TRIG_SRC_CHC_NE   - Channel C negative edge (4-Input only)
#   RP_TRIG_SRC_CHD_PE   - Channel D positive edge (4-Input only)
#   RP_TRIG_SRC_CHD_NE   - Channel D negative edge (4-Input only)
#   RP_TRIG_SRC_EXT_PE   - External trigger positive edge
#   RP_TRIG_SRC_EXT_NE   - External trigger negative edge
#   RP_TRIG_SRC_AWG_PE   - Generator positive edge
#   RP_TRIG_SRC_AWG_NE   - Generator negative edge
trig_src = [rp.RP_TRIG_SRC_CHA_PE, rp.RP_TRIG_SRC_CHB_PE,
            rp.RP_TRIG_SRC_CHC_NE, rp.RP_TRIG_SRC_CHD_NE]

# Available trigger channels (for trigger level):
#   RP_T_CH_1, RP_T_CH_2, RP_T_CH_3, RP_T_CH_4, RP_T_CH_EXT
trig_lvl = [0.1, 0.1, 0.1, 0.1]       # Trigger level in volts per channel
trig_dly = [0, 0, 0, 0]               # Trigger delay in samples per channel

buff_size = 6000                        # Number of samples to capture per channel
timeout_seconds = 10                    # Timeout in seconds for trigger waiting


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya and detect board channel count
# ==============================================================================

print("\nInitializing Red Pitaya...")

result = rp.rp_InitReset(False)
if result != rp.RP_OK:
    print(f"ERROR: Initialization failed with code {result}")
    exit(1)
print("Red Pitaya initialized")

# Detect number of ADC channels from hardware profile
ret, ch_num = rp_hw_profiles.rp_HPGetFastADCChannelsCount()
if ret != rp.RP_OK:
    print("WARNING: Could not detect channel count, defaulting to 2")
    ch_num = 2

# Channel and trigger-channel enums (sliced to active channel count)
channels = [rp.RP_CH_1, rp.RP_CH_2, rp.RP_CH_3, rp.RP_CH_4][:ch_num]
ch_trig  = [rp.RP_T_CH_1, rp.RP_T_CH_2, rp.RP_T_CH_3, rp.RP_T_CH_4][:ch_num]

# Slice configuration lists to active channel count
dec      = dec[:ch_num]
trig_src = trig_src[:ch_num]
trig_lvl = trig_lvl[:ch_num]
trig_dly = trig_dly[:ch_num]

print("=" * 70)
print("Red Pitaya Split Trigger Acquisition Configuration")
print("=" * 70)
print(f"Board model:         {'STEMlab 125-14 4-Input (4 channels)' if ch_num > 2 else 'Red Pitaya (2 channels)'}")
print(f"Active channels:     {ch_num}")
print(f"Samples per channel: {buff_size}")
print(f"Timeout:             {timeout_seconds} seconds")
print()
print("Channel configuration:")
for i in range(ch_num):
    sample_rate = 125000000 / dec[i] / 1000000
    print(f"  CH{i+1}: Decimation={dec[i]} ({sample_rate:.2f} MS/s), Trigger={trig_src[i]}, Level={trig_lvl[i]} V")
print()
print("NOTE: Split trigger mode allows independent triggering per channel")
print("=" * 70)

# Generate random acquisition order to demonstrate channel independence
trig_ord = np.arange(ch_num)
np.random.shuffle(trig_ord)
print(f"\nMonitoring channels in random order: {[i + 1 for i in trig_ord]}")


# ==============================================================================
# SPLIT TRIGGER MODE ACTIVATION - Enable split trigger mode
# ==============================================================================

print("\nActivating split trigger mode...")

result = rp.rp_AcqSetSplitTrigger(True)
if result != rp.RP_OK:
    print(f"ERROR: Failed to activate split trigger mode with code {result}")
    rp.rp_Release()
    exit(1)

split_trig_state = rp.rp_AcqGetSplitTrigger()[1]
print(f"Split trigger mode: {'ENABLED' if split_trig_state else 'DISABLED'}")

if not split_trig_state:
    print("ERROR: Split trigger mode activation failed")
    rp.rp_Release()
    exit(1)


# ==============================================================================
# CHANNEL CONFIGURATION - Reset and configure each channel
# ==============================================================================

print("\nResetting channels...")

for i in range(ch_num):
    result = rp.rp_AcqResetCh(channels[i])
    if result == rp.RP_OK:
        print(f"  CH{i+1} reset successful")
    else:
        print(f"  WARNING: CH{i+1} reset returned code {result}")

print("\nSetting channel parameters...")

for i in range(ch_num):
    result = rp.rp_AcqSetDecimationFactorCh(channels[i], dec[i])
    if result == rp.RP_OK:
        print(f"  CH{i+1}: Decimation set to {dec[i]}")
    else:
        print(f"  ERROR: CH{i+1} decimation setting failed with code {result}")

    result = rp.rp_AcqSetTriggerLevel(ch_trig[i], trig_lvl[i])
    if result == rp.RP_OK:
        print(f"  CH{i+1}: Trigger level set to {trig_lvl[i]} V")
    else:
        print(f"  ERROR: CH{i+1} trigger level setting failed with code {result}")

    result = rp.rp_AcqSetTriggerDelayCh(channels[i], trig_dly[i])
    if result == rp.RP_OK:
        print(f"  CH{i+1}: Trigger delay set to {trig_dly[i]} samples")
    else:
        print(f"  ERROR: CH{i+1} trigger delay setting failed with code {result}")


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
    result = rp.rp_AcqSetTriggerSrcCh(channels[i], trig_src[i])
    if result == rp.RP_OK:
        print(f"  CH{i+1}: Trigger source set to {trig_src[i]}")
    else:
        print(f"  ERROR: CH{i+1} trigger source setting failed with code {result}")

print("\nAcquisition configured and armed")
print("Waiting for trigger events on each channel...")


# ==============================================================================
# TRIGGER WAITING - Round-robin poll until all channels are triggered
# ==============================================================================
#
# Round-robin polling is used instead of sequential per-channel waiting.
# With sequential waiting, a slow channel could block detection of a fast one,
# causing the fast channel's buffer to wrap around and overwrite trigger data
# before it is read.

print("\nWaiting for trigger events (round-robin polling)...")

timeout_reached = False
triggered = [False] * ch_num
filled    = [False] * ch_num

start_time = time.time()
while not all(triggered):
    if time.time() - start_time > timeout_seconds:
        for i in range(ch_num):
            if not triggered[i]:
                print(f"  CH{i+1}: TIMEOUT - No trigger received")
        timeout_reached = True
        break

    for i in trig_ord:
        if triggered[i]:
            continue
        trig_state = rp.rp_AcqGetTriggerStateCh(channels[i])[1]
        if trig_state == rp.RP_TRIG_STATE_TRIGGERED:
            print(f"  CH{i+1}: Trigger detected!")
            triggered[i] = True

print("\nWaiting for buffers to fill (round-robin polling)...")

start_time = time.time()
while not all(filled) and not timeout_reached:
    if time.time() - start_time > timeout_seconds:
        for i in range(ch_num):
            if not filled[i]:
                print(f"  CH{i+1}: TIMEOUT - Buffer fill timeout")
        timeout_reached = True
        break

    for i in trig_ord:
        if filled[i]:
            continue
        if rp.rp_AcqGetBufferFillStateCh(channels[i])[1]:
            print(f"  CH{i+1}: Buffer filled!")
            filled[i] = True

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
    buffers = np.empty((ch_num, buff_size), dtype=np.float32)

    for i in range(ch_num):
        # Use the write pointer at the moment of trigger, not the current pointer
        trigger_pos[i] = rp.rp_AcqGetWritePointerAtTrigCh(channels[i])[1]

        result = rp.rp_AcqGetDataVNP(channels[i], trigger_pos[i], buffers[i])
        if result == rp.RP_OK:
            print(f"  CH{i+1}: Retrieved {buff_size} samples (trigger pos: {trigger_pos[i]})")
        else:
            print(f"  ERROR: CH{i+1} data retrieval failed with code {result}")

    print("\nData statistics:")
    for i in range(ch_num):
        print(f"  CH{i+1}: Range={buffers[i].min():.6f} V to {buffers[i].max():.6f} V, Mean={buffers[i].mean():.6f} V")

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

rp.rp_Release()

print("Resources released - program complete")
print("\nNote: Captured data is displayed above")
print("      For further analysis, save buffers array to file or plot it")
