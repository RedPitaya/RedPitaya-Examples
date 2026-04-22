#!/usr/bin/python3

import sys
import time
import os
import matplotlib.pyplot as plot

sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
import redpitaya_scpi as scpi


rp_s = scpi.scpi("127.0.0.1")
rp_s.tx_txt('RP:LOG CONSOLE')
rp_s.tx_txt('GEN:RST')
rp_s.tx_txt('ACQ:RST')

rp_s.tx_txt('SOUR1:FUNC SINE');
rp_s.tx_txt('SOUR1:FREQ:FIX 1000');
rp_s.tx_txt('SOUR1:VOLT 1');

rp_s.tx_txt('SOUR1:BURS:STAT BURST');
rp_s.tx_txt('SOUR1:BURS:NCYC 1');

rp_s.tx_txt('ACQ:DEC 64');
rp_s.tx_txt('ACQ:TRIG:LEV 0');
rp_s.tx_txt('ACQ:TRIG:DLY 0');


rp_s.tx_txt('ACQ:START')
time.sleep(1)
rp_s.tx_txt('ACQ:TRIG AWG_PE')
rp_s.tx_txt('OUTPUT1:STATE ON');
rp_s.tx_txt('SOUR1:TRIG:INT');

rp_s.tx_txt('ACQ:TRIG:INT:STAT? 1000')
result = rp_s.rx_txt()
if result == 'TIMEOUT':
    print("TIMOUT")
    exit(1)

rp_s.tx_txt('ACQ:TRIG:INT:FILL? 1000')
result = rp_s.rx_txt()
if result == 'TIMEOUT':
    print("TIMOUT")
    exit(1)

rp_s.tx_txt('ACQ:SOUR1:DATA?')
buff_string = rp_s.rx_txt()
buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
buff = list(map(float, buff_string))

plot.plot(buff)
plot.ylabel('Voltage')
plot.show()
