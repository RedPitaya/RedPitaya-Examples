#!/usr/bin/python3

"""
Red Pitaya C++ API example - Two-thread trigger timing measurement
Port to Python
"""

import time
import signal
import threading
import sys
from rp_overlay import overlay
import rp

# Global flag for running state
running = True

def signal_handler(sig, frame):
    global running
    print("\nCtrl+C pressed. Stopping...")
    running = False

def generator_thread():
    """Generator thread - generates periodic trigger signals"""
    print("Generator thread started")

    # Reset and configure generator
    rp.rp_GenReset()
    rp.rp_GenWaveform(rp.RP_CH_1, rp.RP_WAVEFORM_SINE)
    rp.rp_GenFreq(rp.RP_CH_1, 1000.0)
    rp.rp_GenAmp(rp.RP_CH_1, 1.0)
    rp.rp_GenMode(rp.RP_CH_1, rp.RP_GEN_MODE_BURST)
    rp.rp_GenBurstCount(rp.RP_CH_1, 1)
    rp.rp_GenOutEnable(rp.RP_CH_1)

    global running
    while running:
        # Generate trigger
        rp.rp_GenTriggerOnly(rp.RP_CH_1)
        print("Gen signal")
        time.sleep(1)

    print("Generator thread stopped")

def acquisition_thread():
    """Acquisition thread - measures time between triggers"""
    print("Acquisition thread started")
#    rp.rp_EnableDebugReg()

    # Reset and configure acquisition
    rp.rp_AcqReset()
    rp.rp_AcqSetDecimation(rp.RP_DEC_1024)
    rp.rp_AcqSetTriggerDelay(0)
    rp.rp_AcqSetTriggerLevel(rp.RP_T_CH_1, 0.15)
    rp.rp_AcqSetInitTimestamp(0)

    prev_timestamp = 0


    global running
    while running:
        # Start acquisition
        rp.rp_AcqStart()

        # Set trigger source to channel 1 positive edge
        rp.rp_AcqSetTriggerSrc(rp.RP_TRIG_SRC_CHA_PE)

        # Wait for trigger with 3000 ms timeout
        result = rp.rp_AcqIntTriggerRead(4000)

        if not running:
            break

        if result == rp.RP_OK:
            # Get timestamp
            ret, cur_timestamp = rp.rp_AcqGetTimestamp(rp.RP_CH_1)

            if ret == rp.RP_OK:
                if prev_timestamp != 0:
                    delta_time = (cur_timestamp - prev_timestamp) / 1e9
                    print(f"Time between triggers: {delta_time:.6f} s")
                else:
                    print("First trigger detected")

                prev_timestamp = cur_timestamp
            else:
                print(f"Error getting timestamp: {rp.rp_GetError(ret)}")
                break

        elif result == rp.RP_ETIM:
            print("Timeout", file=sys.stderr)
        else:
            print(f"Error: {rp.rp_GetError(result)}", file=sys.stderr)
            break
        time.sleep(0.1)

    rp.rp_AcqStop()
    print("Acquisition thread stopped")

def main():

    fpga = overlay()

    global running
    # Setup signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize Red Pitaya API
    if rp.rp_Init() != rp.RP_OK:
        print("API initialization failed!", file=sys.stderr)
        return 1

    print("Starting trigger timing measurement...")
    print("Press Ctrl+C to stop")

    # Create and start threads
    gen = threading.Thread(target=generator_thread)
    acq = threading.Thread(target=acquisition_thread)
    gen.start()
    acq.start()

    # Wait for threads to complete
    gen.join()
    acq.join()

    print("Program finished successfully")

    # Release resources
    rp.rp_Release()
    return 0

if __name__ == "__main__":
    sys.exit(main())
