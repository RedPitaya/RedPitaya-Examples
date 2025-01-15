#!/usr/bin/python3

import rp_la

obj = rp_la.CLAController()

obj.loadFromFile("can_dump.bin" ,True ,0)

obj.addDecoder("CAN",rp_la.LA_DECODER_CAN)
f = open("can_settings.json", "r")
obj.setDecoderSettings("CAN",f.read())

print("Settings:")
print(obj.getDecoderSettings("CAN"))

print("\nDecoded data\n")
decode = obj.decode("CAN")
for index in range(len(decode)):
    print(obj.getAnnotation(rp_la.LA_DECODER_CAN,decode[index]['control'])," = ",decode[index])
del obj