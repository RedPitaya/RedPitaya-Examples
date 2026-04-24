#!/usr/bin/python3

"""
Red Pitaya C API example for acquiring data from all 4 channels in split
trigger mode - Ported to Python
"""

import time
import random
import sys
from rp_overlay import overlay
import rp
import rp_hw_profiles
import numpy as np

def main():
    # Initialize Red Pitaya
    fpga = overlay()

    if rp.rp_InitReset(False) != rp.RP_OK:
        print("Rp api init failed!", file=sys.stderr)
        return -1

    # Get number of ADC channels (usually 2 or 4 depending on the model)
    # For 4-channel models (like SDRlab 122-16) it returns 4
    # For 2-channel models (like STEMlab 125-14) it returns 2
    ret, ch_num = rp_hw_profiles.rp_HPGetFastADCChannelsCount()
    if ret != rp.RP_OK:
        ch_num = 4  # Default to 4 if can't get

    # Define channels and their configurations
    channels = [rp.RP_CH_1, rp.RP_CH_2, rp.RP_CH_3, rp.RP_CH_4][:ch_num]
    ch_trig = [rp.RP_T_CH_1, rp.RP_T_CH_2, rp.RP_T_CH_3, rp.RP_T_CH_4][:ch_num]

    # Configuration arrays
    decimation = [64, 64, 64, 64][:ch_num]
    trig_lvl = [0.1, 0.1, 0.1, 0.1][:ch_num]
    trig_dly = [0, 0, 0, 0][:ch_num]
    trig_src = [
        rp.RP_TRIG_SRC_CHA_PE,  # CH1 positive edge
        rp.RP_TRIG_SRC_CHB_PE,  # CH2 positive edge
        rp.RP_TRIG_SRC_CHC_NE,  # CH3 negative edge
        rp.RP_TRIG_SRC_CHD_NE   # CH4 negative edge
    ][:ch_num]

    # Random order for triggers
    trig_ord = list(range(1, ch_num + 1))
    random.shuffle(trig_ord)
    print("Trigger order:", trig_ord)

    # Buffer size
    buff_size = 6001

    # Reserve space for data
    buff = [[] for _ in range(ch_num)]
    for i in range(ch_num):
        buff[i] = [0.0] * buff_size

    # Reset and configure split trigger mode
    rp.rp_AcqReset()
    rp.rp_AcqSetSplitTrigger(True)  # Enable split trigger mode

    # Configure acquisition settings for each channel
    for i in range(ch_num):
        rp.rp_AcqResetCh(channels[i])
        rp.rp_AcqSetDecimationFactorCh(channels[i], decimation[i])
        rp.rp_AcqSetGain(channels[i], rp.RP_LOW)
        rp.rp_AcqSetTriggerLevel(ch_trig[i], trig_lvl[i])
        rp.rp_AcqSetTriggerDelayCh(channels[i], trig_dly[i])
        rp.rp_AcqStartCh(channels[i])                      # Start acquisition
        rp.rp_AcqSetTriggerSrcCh(channels[i], trig_src[i]) # Set trigger source

    # Wait for trigger and buffer full for each channel
    acq_trig_pos = [0] * ch_num

    for i in range(ch_num):
        # Wait for trigger with 3000 ms timeout (adjustable)
        ret = rp.rp_AcqIntFillReadCh(channels[i], 3000)
        print(f"Channel {trig_ord[i]} data acquired ret = {rp.rp_GetError(ret)}")

        if ret != rp.RP_OK:
            print(f"Warning: Channel {trig_ord[i]} acquisition failed",
                  file=sys.stderr)

    # Get trigger positions and data for each channel
    for i in range(ch_num):
        ret, pos = rp.rp_AcqGetWritePointerAtTrigCh(channels[i])
        if ret == rp.RP_OK:
            acq_trig_pos[i] = pos
            print(f"Channel {trig_ord[i]} trig position {acq_trig_pos[i]}")

            # Get data in volts
            # Note: rp_AcqGetDataV expects (channel, pos, size, buffer)
            # In Python API, it might return the data directly
            data = np.zeros(20, dtype=np.float32)
            ret = rp.rp_AcqGetDataVNP(channels[i], acq_trig_pos[i], data)
            if ret == rp.RP_OK:
                buff[i] = data
            else:
                print(f"Error reading channel {trig_ord[i]}: {rp.rp_GetError(ret)}",
                      file=sys.stderr)
        else:
            print(f"Error getting trigger position for channel {trig_ord[i]}",
                  file=sys.stderr)

    # Print first 100 samples from each channel
    for i in range(ch_num):
        print(f"Channel {i + 1}")
        samples_to_print = min(100, len(buff[i]))
        for j in range(samples_to_print):
            print(f"{buff[i][j]:.6f}", end='')
            if j != samples_to_print - 1:
                print(", ", end='')
        print("\n")

    # Release resources
    rp.rp_Release()
    print("Program finished successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())