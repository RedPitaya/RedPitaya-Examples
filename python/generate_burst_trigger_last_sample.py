#!/usr/bin/python3

import sys
import os
import matplotlib.pyplot as plot

sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
import redpitaya_scpi as scpi

rp_s = scpi.scpi('200.0.0.15')

rp_s.tx_txt('ACQ:BUF:SIZE?')
BUFF_SIZE = int(rp_s.rx_txt())

x_list = []
t = []

for i in range(BUFF_SIZE):
    t.append((2 * math.pi * i) / (BUFF_SIZE - 1))

for i in range(BUFF_SIZE):
    if i == BUFF_SIZE - 1:
        val_x = 0.5
    else:
        val_x = math.sin(t[i]) + (1.0/3.0) + math.sin(t[i] * 3)

    val_x = max(-1.0, min(1.0, val_x))

    x_list.append(str(val_x))

x = ", ".join(x_list)


rp_s.tx_txt('GEN:RST')

rp_s.tx_txt('SOUR1:FUNC ARBITRARY')

rp_s.tx_txt('SOUR1:TRAC:DATA:DATA ' + x)

rp_s.tx_txt('SOUR1:VOLT 1')

rp_s.tx_txt('SOUR1:FREQ:FIX 4000')

rp_s.tx_txt('SOUR1:BURS:NCYC 2')
rp_s.tx_txt('SOUR1:BURS:STAT BURST')

rp_s.tx_txt('SOUR1:BURS:USE:LASTSample ON')

rp_s.tx_txt('OUTPUT:STATE ON')
rp_s.tx_txt('SOUR:TRIG:INT')

#print x

rp_s.tx_txt('SOUR1:TRAC:DATA:DATA?')
buff_string = rp_s.rx_txt()
buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
buff = list(map(float, buff_string))

import matplotlib.pyplot as plt
plt.plot(buff)
plt.ylabel('Voltage')
plt.show()
