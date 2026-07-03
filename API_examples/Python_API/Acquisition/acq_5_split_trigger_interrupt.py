#!/usr/bin/python3
"""
Red Pitaya Split Trigger Interrupt-Based Acquisition Example
============================================================

This example demonstrates interrupt-based data acquisition in split trigger mode
on Red Pitaya. Each channel has an independent trigger source and uses a hardware
fill interrupt to signal when its buffer is full, eliminating the need for
polling and reducing CPU usage.

Split trigger interrupt mode is useful for:
- Efficient multi-channel acquisition without CPU polling
- Capturing events on multiple channels with different trigger conditions
- Low-latency, event-driven acquisition pipelines

Features:
- Independent trigger and interrupt configuration per channel
- Hardware buffer-fill interrupt per channel (rp_AcqIntFillReadCh)
- Supports 2-channel or 4-channel (STEMlab 125-14 4-Input) boards
- Configurable decimation, gain, trigger level, and delay per channel
- Configurable timeout for interrupt waiting
- Random acquisition order to demonstrate channel independence

Hardware Requirements:
- Red Pitaya board:
  * Any Red Pitaya board (2 channels: CH1, CH2)
  * STEMlab 125-14 4-Input (4 channels: CH1, CH2, CH3, CH4)
- Signal sources connected to input channels for triggering

Software Requirements:
- Red Pitaya Python API (rp module)
- rp_overlay module (for FPGA overlay)
- rp_hw_profiles module (for channel count detection)
- NumPy library
- OS 2.00 or higher (for split trigger and interrupt support)

Usage:
    python acq_5_split_trigger_interrupt.py

    Connect OUT1 to IN1 (and OUT2 to IN2, etc.) for loopback testing, or
    connect external signal sources to the input channels.
    The program will wait for each channel's fill interrupt, then read data.

Configuration:
    Modify parameters in the CONFIGURATION section:
    - decimation: Decimation factor per channel
    - gain: Input gain per channel (RP_LOW or RP_HIGH)
    - trig_src: Trigger source per channel
    - trig_lvl: Trigger level in volts per channel
    - trig_dly: Trigger delay in samples per channel
    - buff_size: Number of samples to capture per channel
    - timeout_ms: Timeout for fill interrupt in milliseconds

Author: Red Pitaya
Date: May 2026
"""

import sys
import numpy as np
from rp_overlay import overlay
import rp
import rp_hw_profiles


# ==============================================================================
# CONFIGURATION - Set your split trigger acquisition parameters
# ==============================================================================

# Decimation factors for each channel (index 0 = CH1, 1 = CH2, ...)
# Available decimations: 1, 2, 4, 8, 16, 17, 18, ..., 65536
#   Decimation 1  = 125 MS/s
#   Decimation 64 = ~1.95 MS/s
#   Sample rate   = 125 MS/s / decimation
decimation = [64, 64, 64, 64]              # Decimation for CH1, CH2, CH3, CH4

# Input gain per channel
# Available gain settings:
#   RP_LOW  - Low gain (±1 V range)
#   RP_HIGH - High gain (±20 V range)
gain = [rp.RP_LOW, rp.RP_LOW, rp.RP_LOW, rp.RP_LOW]

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
trig_lvl = [0.1, 0.1, 0.1, 0.1]           # Trigger level in volts per channel
trig_dly = [0, 0, 0, 0]                    # Trigger delay in samples per channel

buff_size  = 6000                           # Number of samples to capture per channel
timeout_ms = -1                             # Timeout for fill interrupt in milliseconds


# ==============================================================================
# MAIN
# ==============================================================================

def main():

    # ==============================================================================
    # INITIALIZATION - Initialize FPGA overlay and Red Pitaya API
    # ==============================================================================

    print("\nInitializing FPGA overlay and Red Pitaya...")

    fpga = overlay()

    # Uncomment to enable debug registers if needed
    # rp.rp_EnableDebugReg()

    if rp.rp_InitReset(False) != rp.RP_OK:
        print("ERROR: API initialization failed!", file=sys.stderr)
        return 1
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
    dec      = decimation[:ch_num]
    _gain    = gain[:ch_num]
    _trig_src = trig_src[:ch_num]
    _trig_lvl = trig_lvl[:ch_num]
    _trig_dly = trig_dly[:ch_num]

    print("=" * 70)
    print("Red Pitaya Split Trigger Interrupt-Based Acquisition Configuration")
    print("=" * 70)
    print(f"Board model:         {'STEMlab 125-14 4-Input (4 channels)' if ch_num > 2 else 'Red Pitaya (2 channels)'}")
    print(f"Active channels:     {ch_num}")
    print(f"Samples per channel: {buff_size}")
    print(f"Interrupt timeout:   {timeout_ms} ms")
    print()
    print("Channel configuration:")
    for i in range(ch_num):
        sample_rate = 125000000 / dec[i] / 1000000
        print(f"  CH{i+1}: Decimation={dec[i]} ({sample_rate:.2f} MS/s), "
              f"Trigger={_trig_src[i]}, Level={_trig_lvl[i]} V, Gain={_gain[i]}")
    print()
    print("NOTE: Each channel uses a hardware fill interrupt (no CPU polling)")
    print("=" * 70)

    # Generate random acquisition order to demonstrate channel independence
    trig_ord = np.arange(ch_num)
    np.random.shuffle(trig_ord)
    print(f"\nProcessing channels in random order: {[i + 1 for i in trig_ord]}")


    # ==============================================================================
    # RESET AND SPLIT TRIGGER MODE ACTIVATION
    # ==============================================================================

    print("\nResetting acquisition and activating split trigger mode...")

    rp.rp_AcqReset()

    result = rp.rp_AcqSetSplitTrigger(True)
    if result != rp.RP_OK:
        print(f"ERROR: Failed to activate split trigger mode with code {result}", file=sys.stderr)
        rp.rp_Release()
        return 1

    split_trig_state = rp.rp_AcqGetSplitTrigger()[1]
    print(f"Split trigger mode: {'ENABLED' if split_trig_state else 'DISABLED'}")

    if not split_trig_state:
        print("ERROR: Split trigger mode activation failed", file=sys.stderr)
        rp.rp_Release()
        return 1

    # Enable buffer-fill interrupt for each channel
    for i in range(ch_num):
        # True = interrupt enabled, False = interrupt disabled
        rp.rp_AcqSetIntMaskCh(channels[i], rp.RP_INT_TRIGGER, False)    # Disable trigger interrupt (optional, as we wait for fill interrupt)
        rp.rp_AcqSetIntMaskCh(channels[i], rp.RP_INT_FILL, True)
        print(f"  CH{i+1}: Fill interrupt enabled")


    # ==============================================================================
    # CHANNEL CONFIGURATION - Configure each channel
    # ==============================================================================

    print("\nConfiguring channels...")

    for i in range(ch_num):
        rp.rp_AcqResetCh(channels[i])
        rp.rp_AcqSetDecimationFactorCh(channels[i], dec[i])
        rp.rp_AcqSetGain(channels[i], _gain[i])
        rp.rp_AcqSetTriggerLevel(ch_trig[i], _trig_lvl[i])
        rp.rp_AcqSetTriggerDelayCh(channels[i], _trig_dly[i])
        print(f"  CH{i+1}: Decimation={dec[i]}, Gain={_gain[i]}, "
              f"Level={_trig_lvl[i]} V, Delay={_trig_dly[i]} samples")


    # ==============================================================================
    # ACQUISITION START - Start acquisition and arm triggers
    # ==============================================================================

    print("\nStarting acquisition on all channels...")

    for i in range(ch_num):
        result = rp.rp_AcqStartCh(channels[i])
        if result == rp.RP_OK:
            print(f"  CH{i+1}: Acquisition started")
        else:
            print(f"  ERROR: CH{i+1} acquisition start failed with code {result}")

    print("\nConfiguring trigger sources...")

    for i in range(ch_num):
        result = rp.rp_AcqSetTriggerSrcCh(channels[i], _trig_src[i])
        if result == rp.RP_OK:
            print(f"  CH{i+1}: Trigger source set to {_trig_src[i]}")
        else:
            print(f"  ERROR: CH{i+1} trigger source setting failed with code {result}")

    print("\nAcquisition configured and armed")
    print("Waiting for fill interrupts on each channel...")


    # ==============================================================================
    # INTERRUPT WAIT AND CAPTURE - Wait for fill interrupt per channel
    # ==============================================================================
    #
    # rp_AcqIntFillReadCh blocks until the channel's buffer is full after a
    # trigger event, then returns. This is more efficient than polling
    # rp_AcqGetBufferFillStateCh in a tight loop.
    #
    # Sequential waiting is safe here: once a channel triggers and its buffer
    # fills, the hardware holds the captured data until it is explicitly read.

    print(f"\nWaiting for fill interrupts (timeout: {timeout_ms} ms per channel)...")

    acq_ok = [False] * ch_num

    for idx in trig_ord:
        ret = rp.rp_AcqIntFillReadCh(channels[idx], timeout_ms)
        if ret == rp.RP_OK:
            print(f"  CH{idx+1}: Buffer filled (interrupt received)")
            acq_ok[idx] = True
        elif ret == rp.RP_ETIM:
            print(f"  CH{idx+1}: TIMEOUT - No fill interrupt received", file=sys.stderr)
        else:
            print(f"  CH{idx+1}: ERROR - {rp.rp_GetError(ret)}", file=sys.stderr)


    # ==============================================================================
    # DATA RETRIEVAL - Read captured data from each channel
    # ==============================================================================

    print("\nRetrieving captured data...")

    buffers = np.empty((ch_num, buff_size), dtype=np.float32)
    trig_pos = [0] * ch_num
    any_ok = False

    for i in range(ch_num):
        if not acq_ok[i]:
            print(f"  CH{i+1}: Skipped (acquisition did not complete)")
            continue

        ret, trig_pos[i] = rp.rp_AcqGetWritePointerAtTrigCh(channels[i])
        if ret != rp.RP_OK:
            print(f"  CH{i+1}: ERROR getting trigger position: {rp.rp_GetError(ret)}", file=sys.stderr)
            continue

        result = rp.rp_AcqGetDataVNP(channels[i], trig_pos[i], buffers[i])
        if result == rp.RP_OK:
            print(f"  CH{i+1}: Retrieved {buff_size} samples (trigger pos: {trig_pos[i]})")
            any_ok = True
        else:
            print(f"  CH{i+1}: ERROR reading data: {rp.rp_GetError(result)}", file=sys.stderr)

    if any_ok:
        print("\nData statistics:")
        for i in range(ch_num):
            if acq_ok[i]:
                print(f"  CH{i+1}: Range={buffers[i].min():.6f} V to {buffers[i].max():.6f} V, "
                      f"Mean={buffers[i].mean():.6f} V")

        print("\nFirst 10 samples from each channel:")
        for i in range(ch_num):
            if acq_ok[i]:
                print(f"\n  CH{i+1}:")
                for j in range(min(10, buff_size)):
                    print(f"    Sample [{j}]: {buffers[i][j]:.6f} V")
    else:
        print("ERROR: No data acquired - check signal connections and trigger conditions")


    # ==============================================================================
    # DATA OUTPUT - Display full data arrays
    # ==============================================================================

    if any_ok:
        print("\nFull data arrays:")
        for i in range(ch_num):
            if acq_ok[i]:
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

    return 0


if __name__ == "__main__":
    sys.exit(main())