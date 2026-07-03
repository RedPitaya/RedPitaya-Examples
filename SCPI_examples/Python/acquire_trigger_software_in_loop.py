#!/usr/bin/python3

"""
Red Pitaya SCPI example - Acquiring a signal with software trigger in loop
Exact port of the C API example
"""

import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
import redpitaya_scpi as scpi

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 acquire_trigger_software_in_loop.py <red_pitaya_ip>")
        return 1

    ip_address = sys.argv[1]

    # Initialize Red Pitaya
    rp_s = scpi.scpi(ip_address)
    # Configure generator
    print("Configuring generator...")
    rp_s.tx_txt('GEN:RST')
    rp_s.tx_txt('SOUR1:FREQ:FIX 1000')
    rp_s.tx_txt('SOUR1:VOLT 1')
    rp_s.tx_txt('SOUR1:FUNC SINE')
    rp_s.tx_txt('OUTPUT1:STATE ON')
    rp_s.tx_txt('SOUR1:TRIG:INT')

    # Buffer size
    N = 20

    # Configure acquisition
    rp_s.tx_txt('ACQ:RST')
    rp_s.tx_txt('ACQ:DEC 1024')
    rp_s.tx_txt('ACQ:TRIG:DLY 0')

    # Number of acquisition cycles
    count = 10

    for step in range(1, count + 1):
        print(f"\nStep {step}")

        # Start acquisition
        rp_s.tx_txt('ACQ:START')

        # Wait for pre-trigger buffer to fill
        print("Waiting for pre-trigger buffer...")
        for _ in range(5):
            rp_s.tx_txt('ACQ:TRIG:PRE:COUNTER?')
            pre_counter = rp_s.rx_txt()
            print(f"Pre-trigger counter: {pre_counter}")
            time.sleep(1)

        # Additional delay
        time.sleep(1)

        # Set software trigger
        print("Setting software trigger...")
        rp_s.tx_txt('ACQ:TRIG NOW')

        # Wait for trigger to occur
        print("Waiting for trigger...")
        while True:
            rp_s.tx_txt('ACQ:TRIG:STAT?')
            state = rp_s.rx_txt()
            if state == 'TD':
                print("Trigger detected!")
                time.sleep(1)
                break
            time.sleep(0.01)

        # Wait for buffer to fill completely
        print("Waiting for buffer to fill...")
        while True:
            rp_s.tx_txt('ACQ:TRIG:FILL?')
            fill_state = rp_s.rx_txt()
            if fill_state == '1':
                print("Buffer is full!")
                break
            time.sleep(0.01)

        # Get data
        print(f"Acquiring data (buffer size: {N})...")
        rp_s.tx_txt(f'ACQ:SOUR1:DATA?')
        buff_string = rp_s.rx_txt()
        buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')

        if len(buff_string) > N:
            buff_string = buff_string[:N]

        print("\nAcquired data:")
        for value in buff_string:
            print(f"{float(value):.6f}")

    # Stop acquisition
    rp_s.tx_txt('ACQ:STOP')

    # Release resources
    rp_s.close()

    print("\nProgram finished successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())