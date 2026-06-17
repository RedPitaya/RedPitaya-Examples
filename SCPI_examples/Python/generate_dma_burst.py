#!/usr/bin/python3

import lib.redpitaya_scpi as scpi
import sys
import math
import numpy as np

rp_s = scpi.scpi(sys.argv[1])

rp_s.tx_txt('GEN:RST')
rp_s.tx_txt('GEN:AXI:START?')
start_addr = int(rp_s.rx_txt())

rp_s.tx_txt('GEN:AXI:SIZE?')
size = int(rp_s.rx_txt())
size =  min(2**19, int(size / 2))

rp_s.tx_txt('SOUR1:AXI:RESERVE ' + str(start_addr) + ',' + str(start_addr + size * 2))

t = [0.0] * size
x = [0.0] * size

for i in range(1, size):
    t[i] = (2 * math.pi) / size * i

for i in range(size):
    x[i] = math.sin(t[i]) + ((1.0 / 3.0) * math.sin(t[i] * 3))


rp_s.tx_txt('SOUR1:AXI:DEC 1')
rp_s.tx_txt('SOUR1:AXI:ENable ON')

# The block size is chosen so that the server can accept the message.
# The size can be reduced, but if it is increased, the server will reject the message.
chunk_size = 2**14

for i in range(0, size, chunk_size):
    end_index = min(i + chunk_size, size)
    chunk = x[i:end_index]
    result_string = ",".join(f"{val:.6f}" for val in chunk)
    rp_s.tx_txt(f'SOUR1:AXI:OFFSET{i}:DATA{len(chunk)} ' + result_string)

rp_s.tx_txt('SOUR1:BURS:STAT BURST')
rp_s.tx_txt('SOUR1:AXI:SET:CALIB')

rp_s.tx_txt('OUTPUT1:STATE ON')
rp_s.tx_txt('SOUR1:TRIG:INT')

rp_s.tx_txt('SOUR1:AXI:RELEASE')