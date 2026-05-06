#!/usr/bin/python3

import time
import numpy as np
from rp_overlay import overlay
import rp

fpga = overlay()

# Uncomment if you need debug registers
# rp.rp_EnableDebugReg()

rp.rp_Init()

channel = rp.RP_CH_1
channel2 = rp.RP_CH_2
waveform = rp.RP_WAVEFORM_SINE
freq = 100000
ampl = 1.0

# Acquisition paramters
dec = rp.RP_DEC_1

trig_lvl = 0.125
trig_dly = 0

acq_trig_sour = rp.RP_TRIG_SRC_CHA_PE
N = 128

rp.rp_GenReset()
rp.rp_AcqReset()

###### Generation #####
# OUT1
print("Gen_start")
rp.rp_GenWaveform(channel, waveform)
rp.rp_GenFreqDirect(channel, freq)
rp.rp_GenAmp(channel, ampl)

# OUT2
rp.rp_GenWaveform(channel2, waveform)
rp.rp_GenFreqDirect(channel2, freq)
rp.rp_GenAmp(channel2, ampl)

# Specify generator trigger source
#rp.rp_GenTriggerSource(channel, rp.RP_GEN_TRIG_SRC_INTERNAL)

# Enable output synchronisation
rp.rp_GenOutEnableSync(True)
rp.rp_GenTriggerOnly(channel)

##### Acquisition #####
# Set Decimation
rp.rp_AcqSetDecimation(rp.RP_DEC_1)

# Set trigger level and delay
rp.rp_AcqSetTriggerLevel(rp.RP_T_CH_1, trig_lvl)
rp.rp_AcqSetTriggerDelay(trig_dly)
rp.rp_AcqSetIntMask(rp.RP_INT_TRIGGER,False)
# rp.rp_AcqSetIntMask(rp.RP_INT_FILL,False)
print(rp.rp_AcqGetIntMask(rp.RP_INT_TRIGGER))
print(rp.rp_AcqGetIntMask(rp.RP_INT_FILL))

# Start Acquisition
print("Acq_start")
rp.rp_AcqStart()
time.sleep(0.1)
# Specify trigger - input 1 positive edge
rp.rp_AcqSetTriggerSrc(acq_trig_sour)
time.sleep(0.1)

ret = rp.rp_AcqIntTriggerRead(1000)
print(f"Trigger IRQ ret = {rp.rp_GetError(ret)}")

ret = rp.rp_AcqIntFillRead(1000)
print(f"Fill IRQ ret = {rp.rp_GetError(ret)}")

print("ACQ get data")
tp=rp.rp_AcqGetWritePointerAtTrig()[1]
# Get data
# RAW
arr_i16 = np.zeros(N, dtype=np.int16)
arr_f = np.zeros(N, dtype=np.float32)
res = rp.rp_AcqGetDataRawNP(rp.RP_CH_1,tp, arr_i16)
# Volts
res = rp.rp_AcqGetDataVNP(rp.RP_CH_1,tp, arr_f)
print(arr_i16)
print(arr_f)

