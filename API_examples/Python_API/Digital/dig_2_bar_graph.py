#!/usr/bin/python3
"""
Red Pitaya LED Bar Graph Example
=================================

This example demonstrates creating a visual bar graph using Red Pitaya's 8 built-in
LEDs. The user can input a percentage value (0-100), and the LEDs will light up
proportionally to represent that percentage as a bar graph display.

Features:
- Interactive percentage input (0-100%)
- Visual bar graph representation using all 8 LEDs
- Two implementation methods: direct register control and macros
- Input validation with error handling
- Real-time LED update based on user input

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Built-in LEDs (LED0-LED7, no external connections required)

Software Requirements:
- Red Pitaya Python API (rp module)

Usage:
    python dig_2_bar_graph.py
    
    Enter percentage values (0-100) when prompted.
    Press Ctrl+C to stop the program.

Note:
    Choose one of the two methods (comment out the other).
    LEDs light up proportionally: 50% = 4 LEDs, 100% = all 8 LEDs

Author: Red Pitaya
"""

import time
import rp


# ==============================================================================
# CONFIGURATION - Set your LED bar graph parameters here
# ==============================================================================

# Bar graph parameters
default_percent = 50            # Default percentage if invalid input provided
update_delay = 0.2              # Delay between updates in seconds

print("=" * 70)
print("Red Pitaya LED Bar Graph Configuration")
print("=" * 70)
print(f"Default percentage:  {default_percent}%")
print(f"Update delay:        {update_delay} seconds")
print("LEDs used:           LED0-LED7 (8 LEDs total)")
print("Enter percentage values (0-100) when prompted")
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
# LED BAR GRAPH CONTROL - Display percentage as LED bar graph
# ==============================================================================

print("\nStarting LED bar graph...")
print("Choose one of two methods below (comment out the other)\n")


# METHOD 1: Direct register manipulation
# Calculate LED state by summing bit values for the percentage
try:
    print("Method 1: Using direct register control")
    
    # LED bit masks for each of the 8 LEDs
    led_array = [0b00000001, 0b00000010, 0b00000100, 0b00001000, 
                 0b00010000, 0b00100000, 0b01000000, 0b10000000]
    
    while True:
        # Get user input
        percent = input("\nEnter LED bar percentage (0-100): ")
        
        # Validate input
        try:
            percent = int(percent)
            is_valid = True
        except ValueError:
            print("Invalid input - please enter a number between 0 and 100")
            is_valid = False
        
        if is_valid:
            # Clamp percentage to valid range
            if not 0 <= percent <= 100:
                print(f"Value out of range - using default: {default_percent}%")
                percent = default_percent
            
            print(f"Bar showing {percent}%")
            
            # Calculate which LEDs should be on
            led = 0
            for i in range(8):
                # Turn on LED if percentage exceeds threshold for this LED
                # Each LED represents 1/9th of the range (11.11%)
                if percent > (i + 1) * (100.0 / 9):
                    led += led_array[i]     # Add bit to register value
            
            # Set all LEDs at once using calculated register value
            rp.rp_LEDSetState(led)
        
        time.sleep(update_delay)
except KeyboardInterrupt:
    print("\n\nKeyboard interrupt detected (Ctrl+C)")

# METHOD 2: Using convenience macros
# Control each LED individually using pre-defined macros (recommended)
# Uncomment this block and comment the METHOD 1 block above to use
"""
try:
    print("Method 2: Using convenience macros")
    
    # LED array with macro definitions for all 8 LEDs
    led_array = [rp.RP_LED0, rp.RP_LED1, rp.RP_LED2, rp.RP_LED3,
                 rp.RP_LED4, rp.RP_LED5, rp.RP_LED6, rp.RP_LED7]
    
    while True:
        # Get user input
        percent = input("\nEnter LED bar percentage (0-100): ")
        
        # Validate input
        try:
            percent = int(percent)
            is_valid = True
        except ValueError:
            print("Invalid input - please enter a number between 0 and 100")
            is_valid = False
        
        if is_valid:
            # Clamp percentage to valid range
            if not 0 <= percent <= 100:
                print(f"Value out of range - using default: {default_percent}%")
                percent = default_percent
            
            print(f"Bar showing {percent}%")
            
            # Set each LED individually based on percentage
            for i in range(8):
                # Turn on LED if percentage exceeds threshold for this LED
                # Each LED represents 1/9th of the range (11.11%)
                if percent > (i + 1) * (100.0 / 9):
                    rp.rp_DpinSetState(led_array[i], rp.RP_HIGH)
                else:
                    rp.rp_DpinSetState(led_array[i], rp.RP_LOW)
        
        time.sleep(update_delay)

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
