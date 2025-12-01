#!/usr/bin/python3

import rp_la
import rp_hw
import rp_hw_profiles
import numpy as np
from rp_overlay import overlay

class Callback(rp_la.CLACallback):
    def captureStatus(self,controller,isTimeout,bytes,samples,preTrig, postTrig):
        print("CaptureStatus timeout =",isTimeout,"bytes =",bytes,"samples =",samples,"preTrig =",preTrig,"postTrig =",postTrig)

    def decodeDone(self,controller,name):
        print("Decode done ",name)

print("Before the test, connect the output UART TX (E2) <-> DIO0_P (E1) !!!")

baudrate = 115200
decimate = 16
acq_rate = int(rp_hw_profiles.rp_HPGetBaseSpeedHzOrDefault() / decimate)

fpga = overlay("logic")

obj = rp_la.CLAController()
obj.initFpga()

callback = Callback()
obj.setDelegate(callback.__disown__())

obj.setEnableRLE(True)
obj.setDecimation(decimate)
obj.setTrigger(0,rp_la.LA_RISING_OR_FALLING)
obj.setPreTriggerSamples(1000)
obj.setPostTriggerSamples(300000)

obj.addDecoder("UART",rp_la.LA_DECODER_UART)
obj.setDecoderSettingsUInt("UART","rx", 1) # set 1 - first line.  Valid values ​​are from 1 to 8
obj.setDecoderSettingsUInt("UART","baudrate", baudrate)
obj.setDecoderSettingsUInt("UART","num_data_bits", 8)
obj.setDecoderSettingsUInt("UART","parity", 2)
obj.setDecoderSettingsUInt("UART","num_stop_bits", 2)
obj.setDecoderSettingsUInt("UART","acq_speed", acq_rate)

obj.runAsync(0)
print("Started acquire data")

# Write to UART
rp_hw.rp_UartInit()
rp_hw.rp_UartSetSpeed(baudrate)
rp_hw.rp_UartSetBits(rp_hw.RP_UART_CS8)
rp_hw.rp_UartSetStopBits(rp_hw.RP_UART_STOP1)
rp_hw.rp_UartSetParityMode(rp_hw.RP_UART_ODD)
rp_hw.rp_UartSetSettings()
buff = rp_hw.Buffer(10)
buff_size = 3
buff[0] = 1
buff[1] = 2
buff[2] = 3
rp_hw.rp_UartWrite(buff,buff_size)

# wait FPGA
res = obj.wait(1000)
if (res):
    print("Exit by timeout")
    exit(1)

# save data to file
obj.saveCaptureDataToFile("/tmp/data.bin")

rawBytesCount = obj.getCapturedDataSize()
raw_data = np.zeros(rawBytesCount, dtype=np.uint8)
print("Packed samples count:",obj.getDataNP(raw_data))

rle_data = np.zeros(obj.getCapturedSamples(), dtype=np.uint8)
print("Unpacked samples count:",obj.getUnpackedRLEDataNP(rle_data))
print("RLE DATA", raw_data)
print("UNPACKED DATA",rle_data,"\n")

obj.printRLE(False)

print("\nDecoded data")
decode = obj.getDecodedData("UART")
for index in range(len(decode)):
    print(obj.getAnnotation(rp_la.LA_DECODER_UART,decode[index]['control'])," = ",decode[index])

del obj
