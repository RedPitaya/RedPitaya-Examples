#!/usr/bin/python3
"""
Red Pitaya Push Button (Digital Input) Example
===============================================

This example demonstrates reading digital input states from Red Pitaya's DIO_N
pins and displaying them on the corresponding LEDs. Each DIO_N pin's state is
mirrored on its corresponding LED, creating a visual indicator of input states.

This is useful for interfacing with push buttons, switches, or other digital
input devices to provide immediate visual feedback.

Features:
- Reads all 8 DIO_N digital input pins (DIO0_N through DIO7_N)
- Displays input state on corresponding LEDs (LED0-LED7)
- Real-time monitoring with configurable update rate
- Two implementation methods: direct register control and macros
- Input mirroring: HIGH input = LED ON, LOW input = LED OFF

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Optional: Push buttons, switches, or other digital input devices connected to DIO_N pins
- Built-in LEDs (LED0-LED7)

Software Requirements:
- Red Pitaya Python API (rp module)

Usage:
    python dig_4_push_button.py
    
    Connect digital input sources to DIO_N pins (E2 connector).
    Observe corresponding LEDs reflecting the input states.
    Press Ctrl+C to stop the program.

Important Note:
    Red Pitaya GPIO pins default to HIGH state when left floating (not connected).
    Connect inputs to GND to read LOW state, or to 3.3V for HIGH state.
    Do not exceed 3.3V on any GPIO pin to avoid damage.

Pinout Reference:
    DIO0_N - DIO7_N: Extension connector E2, pins [N-pins]
    See Red Pitaya documentation for exact pin locations.

Author: Red Pitaya
"""

import time
import rp


# ==============================================================================
# CONFIGURATION - Set your digital input monitoring parameters here
# ==============================================================================

# Monitoring parameters
update_interval = 0.2           # Time between input reads in seconds
num_inputs = 8                  # Number of DIO_N inputs to monitor (0-7)

print("=" * 70)
print("Red Pitaya Digital Input (Push Button) Configuration")
print("=" * 70)
print(f"Update interval:     {update_interval} seconds")
print(f"Inputs monitored:    DIO0_N through DIO{num_inputs-1}_N")
print(f"LEDs used:           LED0 through LED{num_inputs-1}")
print()
print("Note: GPIO pins default to HIGH when floating (not connected)")
print("      Connect to GND for LOW, 3.3V for HIGH (max voltage)")
print()
print("Press Ctrl+C to stop")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya
# ==============================================================================

print("\nInitializing Red Pitaya...")

# Initialize the Red Pitaya interface
rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# GPIO CONFIGURATION - Configure DIO_N pins as inputs
# ==============================================================================

print("\nConfiguring GPIO pins...")


# ==============================================================================
# INPUT MONITORING - Read digital inputs and mirror to LEDs
# ==============================================================================

print("\nStarting input monitoring...")
print("Choose one of two methods below (comment out the other)\n")


# METHOD 1: Direct register manipulation
# Read all inputs at once from register and process with bitwise operations

try:
    print("Method 1: Using direct register control")
    
    # Bit masks for each DIO_N input
    diox_n = [0b00000001, 0b00000010, 0b00000100, 0b00001000,
              0b00010000, 0b00100000, 0b01000000, 0b10000000]
    
    # Set all DIO*_N pins to inputs (0 = input, 1 = output)
    rp.rp_GPIOnSetDirection(0b00000000)
    print("All DIO_N pins configured as inputs")
    
    # Transfer each digital input state to the corresponding LED
    print("Monitoring inputs - LED will mirror input state...")
    
    while True:
        led = 0
        
        # Read all DIO_N input states at once
        state = rp.rp_GPIOnGetState()[1]
        
        # Process each input bit and build LED register value
        for i in range(num_inputs):
            # Isolate each DIOx_N input state using bitwise AND
            led += (state & diox_n[i])
        
        # Update all LEDs at once with mirrored input states
        rp.rp_LEDSetState(led)
        
        time.sleep(update_interval)

except KeyboardInterrupt:
    print("\n\nKeyboard interrupt detected (Ctrl+C)")

# METHOD 2: Using convenience macros
# Read each input individually using pre-defined macros (recommended)
# Uncomment this block and comment the METHOD 1 block above to use
"""
try:
    print("Method 2: Using convenience macros")
    
    # Arrays of DIO_N input pins and corresponding LEDs
    diox_n = [rp.RP_DIO0_N, rp.RP_DIO1_N, rp.RP_DIO2_N, rp.RP_DIO3_N,
              rp.RP_DIO4_N, rp.RP_DIO5_N, rp.RP_DIO6_N, rp.RP_DIO7_N]
    led_array = [rp.RP_LED0, rp.RP_LED1, rp.RP_LED2, rp.RP_LED3,
                 rp.RP_LED4, rp.RP_LED5, rp.RP_LED6, rp.RP_LED7]
    
    # Configure each DIO_N pin as input
    for i in range(num_inputs):
        rp.rp_DpinSetDirection(diox_n[i], rp.RP_IN)
    print(f"DIO0_N through DIO{num_inputs-1}_N configured as inputs")
    
    # Transfer each digital input state to the corresponding LED
    print("Monitoring inputs - LEDs will mirror input states...")
    
    while True:
        # Read each input and update corresponding LED
        for i in range(num_inputs):
            # Get state of DIOx_N input (returns HIGH or LOW)
            state = rp.rp_DpinGetState(diox_n[i])[1]
            
            # Transfer input state directly to corresponding LED
            rp.rp_DpinSetState(led_array[i], state)
        
        time.sleep(update_interval)
except KeyboardInterrupt:
    print("\n\nKeyboard interrupt detected (Ctrl+C)")
"""


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("Cleaning up...")

# Turn off all LEDs before exiting
rp.rp_LEDSetState(0b00000000)

# Release Red Pitaya resources
rp.rp_Release()

print("Resources released - program complete")
print("All LEDs should now be off")
