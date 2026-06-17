#!/usr/bin/python3
"""
Red Pitaya Logic Analyzer - CAN Bus FPGA Loopback Example
==========================================================

IMPORTANT NOTE:
===============
An FPGA loopback example for the CAN protocol is NOT POSSIBLE because the
Logic Analyzer and the CAN protocol share the same digital pins on Red Pitaya.
This means you cannot simultaneously use the CAN interface and capture its
signals with the Logic Analyzer.

Alternative Approaches:
=======================
If you need to analyze CAN bus traffic on Red Pitaya:

1. External CAN Transceiver:
   - Use an external CAN transceiver connected to different DIO pins
   - Monitor the CAN RX/TX signals with the Logic Analyzer on separate pins
   - This requires additional hardware and wiring

2. File-Based Decoding:
   - Capture CAN data using external equipment or another Red Pitaya
   - Save the captured data to a file
   - Use the file_decode_1_can.py example to decode the saved data

3. Standalone CAN Examples:
   - Refer to CAN-specific examples in the RedPitaya-Examples repository
   - These examples show CAN bus communication without Logic Analyzer

Hardware Limitation:
====================
Red Pitaya's FPGA has resource sharing between peripherals:
- CAN controller uses specific DIO pins
- Logic Analyzer also requires access to DIO pins
- Both cannot access the same pins simultaneously

For CAN bus development and debugging, consider:
- Using two Red Pitaya boards (one for CAN, one for Logic Analyzer)
- External Logic Analyzers with CAN protocol decode capability
- CAN bus analyzers with dedicated hardware

See Also:
=========
- file_decode_1_can.py: Decode CAN data from captured files
- Other protocol examples: I2C, SPI, UART support FPGA loopback

Author: Red Pitaya
Date: January 2026
"""

# This file intentionally contains no executable code due to hardware limitations
print("=" * 70)
print("CAN Bus FPGA Loopback Example - NOT SUPPORTED")
print("=" * 70)
print("\n!! HARDWARE LIMITATION !!")
print("\nAn FPGA loopback example for the CAN protocol is not possible")
print("because the Logic Analyzer and the CAN protocol share the same")
print("digital pins on Red Pitaya.")
print("\nAlternative options:")
print("  1. Use file_decode_1_can.py to decode pre-captured CAN data")
print("  2. Use external CAN transceiver on different DIO pins")
print("  3. Use two Red Pitaya boards (one for CAN, one for LA)")
print("  4. Refer to standalone CAN examples in RedPitaya-Examples")
print("\n" + "=" * 70)
