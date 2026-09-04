#!/usr/bin/python3

import sys
import numpy as np
import rp_hw

uart_speed = 115200                     # Baud rate in bps
uart_timeout = 10                       # Read timeout in 1/10 sec (10 = 1 sec)
uart_word_size = rp_hw.RP_UART_CS8      # Word size (CS6, CS7, CS8)
uart_parity = rp_hw.RP_UART_MARK        # Parity (NONE, EVEN, ODD, MARK, SPACE)
uart_stop_bits = rp_hw.RP_UART_STOP2    # Stop bits (STOP1, STOP2)

# Test Data
test_message = "TEST string"            # Message to send via UART
read_chunk_1_size = 5                   # Size of first read chunk (bytes)

# Get parameter names for display
word_size_names = {
    rp_hw.RP_UART_CS6: "6 bits",
    rp_hw.RP_UART_CS7: "7 bits",
    rp_hw.RP_UART_CS8: "8 bits"
}

parity_names = {
    rp_hw.RP_UART_NONE: "None",
    rp_hw.RP_UART_EVEN: "Even",
    rp_hw.RP_UART_ODD: "Odd",
    rp_hw.RP_UART_MARK: "Mark",
    rp_hw.RP_UART_SPACE: "Space"
}

stop_bits_names = {
    rp_hw.RP_UART_STOP1: "1 bit",
    rp_hw.RP_UART_STOP2: "2 bits"
}

print("=" * 70)
print("Red Pitaya UART Loopback Test Configuration")
print("=" * 70)
print(f"Baud Rate:           {uart_speed} bps")
print(f"Timeout:             {uart_timeout / 10:.1f} seconds")
print(f"Word Size:           {word_size_names.get(uart_word_size, 'Unknown')}")
print(f"Parity:              {parity_names.get(uart_parity, 'Unknown')}")
print(f"Stop Bits:           {stop_bits_names.get(uart_stop_bits, 'Unknown')}")
print(f"Test Message:        \"{test_message}\"")
print(f"Message Length:      {len(test_message)} bytes")
print(f"Read Strategy:       First {read_chunk_1_size} bytes, then remainder")
print("=" * 70)


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """Main program to perform UART loopback test."""

    try:
        # Prepare test data
        data_int = [ord(char) for char in test_message]
        data_size = len(data_int)

        # ===== STEP 1: Initialize UART =====
        print("\n[1] Initializing UART interface...")
        rp_hw.rp_UartInit()
        print("    UART interface initialized")

        # ===== STEP 2: Configure UART Parameters =====
        print("\n[2] Configuring UART parameters...")

        rp_hw.rp_UartSetTimeout(uart_timeout)
        print(f"    Timeout: {uart_timeout / 10:.1f} seconds")

        rp_hw.rp_UartSetSpeed(uart_speed)
        print(f"    Baud rate: {uart_speed} bps")

        rp_hw.rp_UartSetBits(uart_word_size)
        print(f"    Word size: {word_size_names.get(uart_word_size, 'Unknown')}")

        rp_hw.rp_UartSetStopBits(uart_stop_bits)
        print(f"    Stop bits: {stop_bits_names.get(uart_stop_bits, 'Unknown')}")

        rp_hw.rp_UartSetParityMode(uart_parity)
        print(f"    Parity: {parity_names.get(uart_parity, 'Unknown')}")

        # ===== STEP 3: Apply Settings =====
        print("\n[3] Applying UART settings...")
        rp_hw.rp_UartSetSettings()
        print("    Settings applied successfully")

        # ===== STEP 4: Prepare TX Buffer =====
        print("\n[4] Preparing transmit buffer...")
        tx_buff = np.array(data_int, dtype=np.uint8)  # Convert message to byte array
        print(f"    TX Buffer: {data_size} bytes - \"{test_message}\"")

        # ===== STEP 5: Write Data to UART =====
        print("\n[5] Transmitting data via UART...")
        rp_hw.rp_UartWrite(tx_buff)
        print(f"    {data_size} bytes transmitted")
        
        # ===== STEP 6: Read First Chunk =====
        print(f"\n[6] Reading first {read_chunk_1_size} bytes...")
        res_1, rx_buff = rp_hw.rp_UartRead(read_chunk_1_size)
                
        print(f"    Result code: {res_1}")
        print(f"    Bytes read: {rx_buff.size}")
                
        if rx_buff.size > 0:
                data_chunk_1 = rx_buff.tobytes()  # Keep as bytes
                print(f"    Data (hex): {data_chunk_1.hex()}")  # Print as hexadecimal
                # Or print as raw bytes if needed:
                print(f"    Data (raw): {data_chunk_1}")
        else:
                data_chunk_1 = b""  # Empty bytes
                print("    WARNING: No data received")

        # ===== STEP 7: Read Remaining Data =====
        remaining_bytes = data_size - read_chunk_1_size
        print(f"\n[7] Reading remaining {remaining_bytes} bytes...")
        res_2, rx_buff = rp_hw.rp_UartRead(remaining_bytes)
        result_code_2 = res_2
        bytes_read_2 = rx_buff.size
        
        print(f"    Result code: {result_code_2}")
        print(f"    Bytes read: {bytes_read_2}")
            
        if bytes_read_2 > 0:
                data_chunk_2 = rx_buff.tobytes()  # Keep as bytes
                print(f"    Data (hex): {data_chunk_1.hex()}")  # Print as hexadecimal
                # Or print as raw bytes if needed:
                print(f"    Data (raw): {data_chunk_2}")
        else:
                data_chunk_2 = b""  # Empty bytes
                print("    WARNING: No data received")

        # ===== STEP 8: Verify Data =====
        print("\n[8] Verifying loopback data...")
        received_data = data_chunk_1 + data_chunk_2
        total_bytes_read = len(received_data)
        
        print(f"    Total bytes received: {total_bytes_read}/{data_size}")
        print(f"    Received data: \"{received_data}\"")
        
        if received_data == test_message:
            print("    Data verification: MATCH")
            match = True
        else:
            print("    Data verification: MISMATCH")
            print(f"    Expected: \"{test_message}\"")
            print(f"    Received: \"{received_data}\"")
            match = False
        
        # ===== STEP 9: Cleanup =====
        print("\n[9] Cleaning up resources...")
        rp_hw.rp_UartRelease()
        print("    UART resources released")
        
        # ===== COMPLETION =====
        print("\n" + "=" * 70)
        if match:
            print("UART loopback test completed successfully - All data verified")
        else:
            print("UART loopback test completed - Data verification failed")
            print("Check loopback connection (TX to RX)")
        print("=" * 70)
        
        return 0 if match else 1
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Attempt cleanup
        try:
            rp_hw.rp_UartRelease()
        except:
            pass
        
        return 1


if __name__ == "__main__":
    exit(main())
