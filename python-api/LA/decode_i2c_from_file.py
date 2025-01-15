#!/usr/bin/python3

import rp_la

obj = rp_la.CLAController()

obj.loadFromFile("i2c_dump.bin" ,True ,0)

obj.addDecoder("I2C",rp_la.LA_DECODER_I2C)
f = open("i2c_settings.json", "r")
obj.setDecoderSettings("I2C",f.read())

print("Settings:")
print(obj.getDecoderSettings("I2C"))

# Constants for I2C

# enum AddressFormat
# {
# 	Shifted		= 0,
# 	Unshifted	= 1
# };

print("\nDecoded data\n")
decode = obj.decode("I2C")
for index in range(len(decode)):
    print(obj.getAnnotation(rp_la.LA_DECODER_I2C,decode[index]['control'])," = ",decode[index])
del obj