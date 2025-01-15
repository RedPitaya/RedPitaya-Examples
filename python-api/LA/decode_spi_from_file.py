#!/usr/bin/python3

import rp_la

obj = rp_la.CLAController()

obj.loadFromFile("spi_dump.bin" ,True ,0)

obj.addDecoder("SPI",rp_la.LA_DECODER_SPI)
f = open("spi_settings.json", "r")
obj.setDecoderSettings("SPI",f.read())

print("Settings:")
print(obj.getDecoderSettings("SPI"))

# Constants for SPI

# enum CsPolartiy
# {
# 	ActiveLow	= 0,
# 	ActiveHigh	= 1
# };

# enum BitOrder
# {
# 	MsbFirst	= 0,
# 	LsbFirst	= 1
# };

print("\nDecoded data\n")
decode = obj.decode("SPI")
for index in range(len(decode)):
    print(obj.getAnnotation(rp_la.LA_DECODER_SPI,decode[index]['control'])," = ",decode[index])
del obj