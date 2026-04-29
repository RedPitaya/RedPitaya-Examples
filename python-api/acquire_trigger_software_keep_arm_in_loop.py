#!/usr/bin/python3

"""
Red Pitaya C API example - Acquiring a signal with software trigger in loop
Using Keep Arm mode to maintain acquisition between triggers
Ported to Python
"""

import time
import sys
import numpy as np
from rp_overlay import overlay
import rp

def main():
    # Initialize Red Pitaya
    fpga = overlay()

    if rp.rp_Init() != rp.RP_OK:
        print("Rp api init failed!", file=sys.stderr)
        return -1

    # Uncomment if you need debug registers
    # rp.rp_EnableDebugReg()

    # Configure generator
    print("Configuring generator...")
    rp.rp_GenReset()
    rp.rp_GenFreq(rp.RP_CH_1, 100.0)       # 100 Hz frequency
    rp.rp_GenAmp(rp.RP_CH_1, 1.0)           # 1 V amplitude
    rp.rp_GenWaveform(rp.RP_CH_1, rp.RP_WAVEFORM_SINE)
    rp.rp_GenOutEnable(rp.RP_CH_1)
    rp.rp_GenTriggerOnly(rp.RP_CH_1)

    # Buffer size
    N = 20
    arr_f = np.zeros(N, dtype=np.float32)

    # Configure acquisition
    rp.rp_AcqReset()
    rp.rp_AcqSetDecimation(rp.RP_DEC_16384)  # High decimation for slow sampling
    rp.rp_AcqSetTriggerDelay(0)               # No trigger delay

    # Enable Keep Arm mode - acquisition stays armed after trigger
    print("Enabling Keep Arm mode...")
    rp.rp_AcqSetArmKeep(True)

    # Start acquisition once (keeps running due to Keep Arm)
    rp.rp_AcqStart()
    print("Acquisition started in Keep Arm mode\n")

    # Number of acquisition cycles
    count = 10

    for step in range(1, count + 1):
        print(f"Step {step}")

        # Wait for pre-trigger buffer to fill
        print("Waiting for pre-trigger buffer...")
        for _ in range(5):
            ret, pre_counter = rp.rp_AcqGetPreTriggerCounter()
            if ret == rp.RP_OK:
                print(f"  Pre-trigger counter: {pre_counter}")
            time.sleep(1)

        # Additional delay
        time.sleep(1)

        # Set software trigger
        print("Setting software trigger...")
        rp.rp_AcqSetTriggerSrc(rp.RP_TRIG_SRC_NOW)

        # Wait for trigger to occur
        print("Waiting for trigger...")
        while True:
            ret, state = rp.rp_AcqGetTriggerState()
            if ret == rp.RP_OK and state == rp.RP_TRIG_STATE_TRIGGERED:
                print("Trigger detected!")
                time.sleep(1)  # Extra delay after trigger
                break
            time.sleep(0.01)  # Small delay to reduce CPU usage

        # Wait for buffer to fill completely
        print("Waiting for buffer to fill...")
        while True:
            ret, fill_state = rp.rp_AcqGetBufferFillState()
            if ret == rp.RP_OK and fill_state:
                print("Buffer is full!")
                break
            time.sleep(0.01)

        # Get oldest data using NumPy array
        print(f"Acquiring data (buffer size: {N})...")
        res = rp.rp_AcqGetOldestDataVNP(rp.RP_CH_1, arr_f)

        if res == rp.RP_OK:
            print("\nAcquired data:")
            for i, value in enumerate(arr_f):
                print(f"{value:.6f}")
        else:
            print(f"Error acquiring data: {rp.rp_GetError(res)}",
                  file=sys.stderr)
            break

        # Unlock trigger for Keep Arm mode to re-arm for next acquisition
        # In normal mode, unlocking occurs when calling rp_AcqStart
        print("Unlocking trigger for next acquisition...")
        rp.rp_AcqUnlockTrigger()

        print("-" * 50)

    # Stop acquisition
    rp.rp_AcqStop()

    # Release resources
    rp.rp_Release()
    print("\nProgram finished successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())