#!/usr/bin/python3

import time
import numpy as np
from rp_overlay import overlay
import rp

fpga = overlay()
rp.rp_Init()

memory = rp.rp_AcqAxiGetMemoryRegion()
if (memory[0] != rp.RP_OK):
    print("Error get reserved memory")
    exit(1)

dma_start_address = memory[1]
dma_full_size = memory[2]

bufferSize = 1024 * 1024

if (dma_full_size < bufferSize):
    bufferSize = dma_full_size

if (rp.rp_GenAxiReserveMemory(rp.RP_CH_1,dma_start_address, dma_start_address + bufferSize) != rp.RP_OK):
    print("Error setting address for DMA mode for OUT1")
    exit(1)

if (rp.rp_GenAxiSetDecimationFactor(rp.RP_CH_1,1) != rp.RP_OK):
    print("Error setting decimation for generator")
    exit(1)

if (rp.rp_GenAxiSetEnable(rp.RP_CH_1,True) != rp.RP_OK):
    print("Error enable axi mode for OUT1")
    exit(1)

bufferSize = int(bufferSize / 2)

t = np.linspace(0, 2 * np.pi, bufferSize, endpoint=False, dtype=np.float32)
x = np.sin(t) + (1/3) * np.sin(3 * t)

rp.rp_GenSetAmplitudeAndOffsetOrigin(rp.RP_CH_1)
rp.rp_GenMode(rp.RP_CH_1, rp.RP_GEN_MODE_BURST)
rp.rp_GenBurstCount(rp.RP_CH_1, int(2))
rp.rp_GenBurstRepetitions(rp.RP_CH_1, int(2));
rp.rp_GenBurstPeriod(rp.RP_CH_1, int(100));
rp.rp_GenAxiWriteWaveform(rp.RP_CH_1,x)
rp.rp_GenOutEnable(rp.RP_CH_1)
rp.rp_GenTriggerOnly(rp.RP_CH_1)