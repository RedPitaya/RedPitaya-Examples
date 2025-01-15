#!/usr/bin/python3

import rp_la

obj = rp_la.CLAController()

obj.loadFromFile("uart_dump.bin" ,True ,0)

obj.addDecoder("UART",rp_la.LA_DECODER_UART)
f = open("uart_settings.json", "r")
obj.setDecoderSettings("UART",f.read())

print("Settings:")
print(obj.getDecoderSettings("UART"))

# Constants for UART

# enum UartBitOrder
# {
# 	LSB_FIRST = 0,
# 	MSB_FIRST = 1
# };

# enum NumDataBits
# {
# 	DATA_BITS_5 = 5,
# 	DATA_BITS_6 = 6,
# 	DATA_BITS_7 = 7,
# 	DATA_BITS_8 = 8,
# 	DATA_BITS_9 = 9
# };

# enum Parity
# {
# 	NONE 	 = 0,
# 	EVEN 	 = 1,
# 	ODD  	 = 2,
# 	ALWAYS_0 = 3,
# 	ALWAYS_1 = 4
# };

# enum NumStopBits
# {
# 	STOP_BITS_NO = 0,
# 	STOP_BITS_05 = 1,
# 	STOP_BITS_10 = 2,
# 	STOP_BITS_15 = 3,
# 	STOP_BITS_20 = 4
# };

print("\nDecoded data\n")
decode = obj.decode("UART")
for index in range(len(decode)):
    print(obj.getAnnotation(rp_la.LA_DECODER_UART,decode[index]['control'])," = ",decode[index])
del obj
