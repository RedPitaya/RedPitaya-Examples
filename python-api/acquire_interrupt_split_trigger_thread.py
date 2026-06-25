#!/usr/bin/python3
"""
Red Pitaya Python API example for acquiring data from all 4 channels in split
trigger mode with per-channel threads and multiple acquisitions.
"""

import rp
import rp_hw_profiles
import rp_hw_calib
import threading
import time
import numpy as np
from typing import List

# Constants
MAX_NUM = 4
BUFF_SIZE = 6001
TIMEOUT_MS = 3000
ACQUISITIONS_PER_CHANNEL = 5  # Number of acquisitions per channel


class ChannelConfig:
    """Channel configuration structure."""

    def __init__(self):
        self.channel_num = 0  # Channel number: 1, 2, 3, 4
        self.ch = None  # Red Pitaya channel handle
        self.trig = None  # Trigger channel
        self.decimation = 0  # Decimation factor
        self.trig_lvl = 0.0  # Trigger level in Volts
        self.trig_dly = 0  # Trigger delay
        self.src = None  # Trigger source
        self.trig_pos = 0  # Trigger position in buffer
        self.data = np.zeros(BUFF_SIZE, dtype=np.float32)  # Acquired data buffer as numpy array
        self.acquisition_count = 0  # Number of successful acquisitions


# ============================================================
# RED PITAYA INITIALIZATION
# ============================================================

def init_red_pitaya():
    """
    Initialize Red Pitaya hardware and enable split trigger mode.
    Initialization ends with rp_AcqSetSplitTrigger(true).
    Returns True on success, False on failure.
    """
    # Reset Red Pitaya
    if rp.rp_InitReset(False) != rp.RP_OK:
        print("RP init failed!", flush=True)
        return False

    # Initialize calibration
    if rp_hw_calib.rp_CalibInit() != rp_hw_calib.RP_HW_CALIB_OK:
        print("Calibration failed!", flush=True)
        return False

    # Reset acquisition and set split trigger mode
    rp.rp_AcqReset()
    rp.rp_AcqSetSplitTrigger(True)  # <-- INITIALIZATION ENDS HERE

    return True


# ============================================================
# THREAD-SAFE PRINT FUNCTION
# ============================================================

def safe_print(cout_lock: threading.Lock, *args):
    """Thread-safe print function that automatically locks mutex and appends newline."""
    with cout_lock:
        print(*args, flush=True)


# ============================================================
# PER-CHANNEL THREAD FUNCTION
# ============================================================

def channel_thread(cfg: ChannelConfig, thread_id: int, cout_lock: threading.Lock):
    """
    Thread function for a single channel.
    Each thread performs: configuration -> multiple acquisitions -> output.
    """

    # ============================================================
    # STEP 1: CHANNEL CONFIGURATION (done once)
    # ============================================================

    safe_print(cout_lock, f"[THREAD {thread_id}] Configuring channel {cfg.channel_num}")

    # Disable interrupt for trigger point
    rp.rp_AcqSetIntMaskCh(cfg.ch, rp.RP_INT_TRIGGER, False)

    # Reset channel
    rp.rp_AcqResetCh(cfg.ch)

    # Set decimation factor
    rp.rp_AcqSetDecimationFactorCh(cfg.ch, cfg.decimation)

    # Set gain to low range
    rp.rp_AcqSetGain(cfg.ch, rp.RP_LOW)

    # Set trigger level
    rp.rp_AcqSetTriggerLevel(cfg.trig, cfg.trig_lvl)

    # Set trigger delay
    rp.rp_AcqSetTriggerDelayCh(cfg.ch, cfg.trig_dly)

    safe_print(cout_lock, f"[THREAD {thread_id}] Channel {cfg.channel_num} configured")

    # ============================================================
    # STEP 2: MULTIPLE DATA ACQUISITIONS
    # ============================================================

    for acq in range(ACQUISITIONS_PER_CHANNEL):
        # --------------------------------------------------------
        # 2a. START ACQUISITION AND SET TRIGGER SOURCE
        # --------------------------------------------------------

        # Start acquisition on channel
        rp.rp_AcqStartCh(cfg.ch)

        # Set trigger source for channel
        rp.rp_AcqSetTriggerSrcCh(cfg.ch, cfg.src)

        # --------------------------------------------------------
        # 2b. WAIT FOR TRIGGER
        # --------------------------------------------------------

        safe_print(
            cout_lock,
            f"[THREAD {thread_id}] Acquisition {acq + 1}: "
            f"Waiting for trigger on channel {cfg.channel_num}"
        )

        # Wait for trigger and buffer full (timeout in ms)
        ret = rp.rp_AcqIntFillReadCh(cfg.ch, TIMEOUT_MS)

        # Check if trigger was successful
        if ret != rp.RP_OK:
            safe_print(
                cout_lock,
                f"[THREAD {thread_id}] Acquisition {acq + 1}: "
                f"Channel {cfg.channel_num} trigger failed! "
                f"Error: {rp.rp_GetError(ret)}"
            )
            continue  # Skip this acquisition attempt

        safe_print(
            cout_lock,
            f"[THREAD {thread_id}] Acquisition {acq + 1}: "
            f"Channel {cfg.channel_num} triggered, ret = {ret}"
        )

        # --------------------------------------------------------
        # 2c. ACQUIRE DATA
        # --------------------------------------------------------

        safe_print(
            cout_lock,
            f"[THREAD {thread_id}] Acquisition {acq + 1}: "
            f"Acquiring data from channel {cfg.channel_num}"
        )

        # Get trigger position in buffer
        result, cfg.trig_pos = rp.rp_AcqGetWritePointerAtTrigCh(cfg.ch)

        safe_print(
            cout_lock,
            f"[THREAD {thread_id}] Acquisition {acq + 1}: "
            f"Channel {cfg.channel_num} trig pos = {cfg.trig_pos}"
        )

        # Read data from buffer using rp_AcqGetDataVNP with numpy array
        ret = rp.rp_AcqGetDataVNP(cfg.ch, cfg.trig_pos, cfg.data)

        if ret != rp.RP_OK:
            safe_print(
                cout_lock,
                f"[THREAD {thread_id}] Acquisition {acq + 1}: "
                f"Channel {cfg.channel_num} data read failed! "
                f"Error: {rp.rp_GetError(ret)}"
            )
            continue  # Skip this acquisition attempt

        # Increment acquisition counter
        cfg.acquisition_count += 1

        safe_print(
            cout_lock,
            f"[THREAD {thread_id}] Acquisition {acq + 1}: "
            f"Channel {cfg.channel_num} data acquired ({len(cfg.data)} samples)"
        )

        # --------------------------------------------------------
        # 2d. OUTPUT DATA
        # --------------------------------------------------------

        with cout_lock:
            print(
                f"[THREAD {thread_id}] Acquisition {acq + 1}: "
                f"Channel {cfg.channel_num} data:",
                flush=True
            )

            # Print only first 20 samples for brevity
            print_samples = min(20, len(cfg.data))
            formatted_data = ", ".join(f"{cfg.data[j]:.3f}" for j in range(print_samples))
            print(formatted_data, flush=True)
            print(flush=True)

        # Small delay between acquisitions to allow hardware to settle
        time.sleep(0.1)  # 100 ms

    # ============================================================
    # STEP 3: COMPLETION SUMMARY
    # ============================================================

    safe_print(
        cout_lock,
        f"[THREAD {thread_id}] Channel {cfg.channel_num} "
        f"completed {cfg.acquisition_count} acquisitions"
    )


# ============================================================
# MAIN FUNCTION
# ============================================================

def main():
    """Main function to orchestrate multi-channel acquisition."""

    # Get number of available ADC channels
    ch_num = rp_hw_profiles.rp_HPGetFastADCChannelsCountOrDefault()

    # Initialize Red Pitaya hardware
    if not init_red_pitaya():
        return -1

    # ============================================================
    # CHANNEL CONFIGURATION SETUP
    # ============================================================

    # Channel hardware mappings
    ch_list = [rp.RP_CH_1, rp.RP_CH_2, rp.RP_CH_3, rp.RP_CH_4]
    trig_list = [rp.RP_T_CH_1, rp.RP_T_CH_2, rp.RP_T_CH_3, rp.RP_T_CH_4]
    src_list = [
        rp.RP_TRIG_SRC_CHA_PE,  # Channel A positive edge
        rp.RP_TRIG_SRC_CHB_PE,  # Channel B positive edge
        rp.RP_TRIG_SRC_CHC_PE,  # Channel C positive edge
        rp.RP_TRIG_SRC_CHD_PE   # Channel D positive edge
    ]

    # Default configuration values
    dec_list = [64, 64, 64, 64]
    lvl_list = [0, 0, 0, 0]
    dly_list = [0, 0, 0, 0]

    # Create channel configurations
    channels: List[ChannelConfig] = []
    for i in range(ch_num):
        cfg = ChannelConfig()
        cfg.channel_num = i + 1
        cfg.ch = ch_list[i]
        cfg.trig = trig_list[i]
        cfg.decimation = dec_list[i]
        cfg.trig_lvl = lvl_list[i]
        cfg.trig_dly = dly_list[i]
        cfg.src = src_list[i]
        channels.append(cfg)

    # Lock for thread-safe console output
    cout_lock = threading.Lock()

    # Print initial configuration info
    safe_print(cout_lock, f"Acquisitions per channel: {ACQUISITIONS_PER_CHANNEL}")
    safe_print(cout_lock, "")

    # ============================================================
    # START PER-CHANNEL THREADS
    # ============================================================

    threads = []
    for i in range(ch_num):
        thread = threading.Thread(
            target=channel_thread,
            args=(channels[i], i + 1, cout_lock)
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # ============================================================
    # FINAL SUMMARY
    # ============================================================

    safe_print(cout_lock, "")
    safe_print(cout_lock, "[MAIN] ===== SUMMARY =====")

    total_acquisitions = 0
    for cfg in channels:
        safe_print(
            cout_lock,
            f"[MAIN] Channel {cfg.channel_num}: "
            f"{cfg.acquisition_count} acquisitions"
        )
        total_acquisitions += cfg.acquisition_count

    safe_print(cout_lock, f"[MAIN] Total acquisitions: {total_acquisitions}")

    # ============================================================
    # CLEANUP
    # ============================================================

    rp.rp_Release()

    return 0


if __name__ == "__main__":
    exit(main())