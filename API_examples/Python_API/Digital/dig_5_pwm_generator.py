#!/usr/bin/python3
"""
Red Pitaya Digital GPIO - PWM Square Wave Generator with Visualization
======================================================================

This example demonstrates how to generate a configurable PWM (Pulse Width Modulation)
square wave signal on a Red Pitaya digital GPIO pin. It features interactive parameter
adjustment, real-time output generation, and visualization of the generated waveform.

Features:
- Configurable frequency and duty cycle
- Interactive parameter adjustment during runtime
- Real-time square wave output on GPIO pin
- Keyboard interrupt handling for clean exit

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Optional: LED, oscilloscope, or logic analyzer to observe output

GPIO Pin Used:
- DIO1_P (Digital I/O pin 1 Positive) - Square wave output

Software Requirements:
- Red Pitaya Python API (rp module)

Usage:
    python dig_5_pwm_generator.py

Configuration:
    The program will prompt for:
    - Frequency (Hz): PWM frequency
    - Duty cycle (0 to 1): High time as fraction of period
    - Duration (seconds): How long to generate the signal

Example Use Cases:
    - LED dimming control (variable duty cycle)
    - Servo motor control (fixed frequency, variable duty cycle)
    - Digital signal testing
    - Timing reference generation

Note:
    This is a software-based PWM implementation. For precise high-frequency
    PWM, consider using the hardware PWM capabilities of Red Pitaya.

Author: Red Pitaya
Date: January 2026
"""

import rp
import time


# ==============================================================================
# CONSTANTS
# ==============================================================================

OUTPUT_PIN = rp.RP_DIO1_P       # GPIO pin for PWM output
OUTPUT_PIN_NAME = "DIO1_P"      # Pin name for display


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_user_input(prompt, default):
    """
    Get user input with a default value.
    
    Args:
        prompt (str): The prompt message to display
        default (float): Default value if user presses Enter
        
    Returns:
        float: User input value or default
    """
    user_input = input(f"{prompt} (default: {default}): ")
    if not user_input:
        return default
    try:
        return float(user_input)
    except ValueError:
        print(f"  Invalid input - using default: {default}")
        return default


def calculate_timing(pwm_frequency, pwm_duty_cycle):
    """
    Calculate timing parameters for PWM signal.
    
    Args:
        pwm_frequency (float): PWM frequency in Hz
        pwm_duty_cycle (float): Duty cycle (0.0 to 1.0)
        
    Returns:
        tuple: (period, high_time, low_time) in seconds
    """
    period = 1.0 / pwm_frequency
    high_time = period * pwm_duty_cycle
    low_time = period * (1 - pwm_duty_cycle)
    return period, high_time, low_time


def output_square_wave(pwm_frequency, pwm_duty_cycle, pwm_duration):
    """
    Generate a square wave output on GPIO pin.
    
    Args:
        pwm_frequency (float): PWM frequency in Hz
        pwm_duty_cycle (float): Duty cycle (0.0 to 1.0)
        pwm_duration (float): Duration in seconds
    """
    period, high_time, low_time = calculate_timing(pwm_frequency, pwm_duty_cycle)
    
    start_time = time.time()
    
    # Generate square wave for specified duration
    while (time.time() - start_time) < pwm_duration:
        rp.rp_DpinSetState(OUTPUT_PIN, rp.RP_HIGH)
        time.sleep(high_time)
        rp.rp_DpinSetState(OUTPUT_PIN, rp.RP_LOW)
        time.sleep(low_time)


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

print("=" * 70)
print("Red Pitaya - PWM Square Wave Generator")
print("=" * 70)

# Get initial user-defined parameters
print("\nEnter PWM parameters:")
frequency = get_user_input("  Frequency (Hz)", 1)
while frequency <= 0:
    print("  ERROR: Frequency must be greater than 0 Hz")
    frequency = get_user_input("  Frequency (Hz)", 1)

duty_cycle = get_user_input("  Duty cycle (0 to 1)", 0.5)
while not 0.0 <= duty_cycle <= 1.0:
    print("  ERROR: Duty cycle must be between 0.0 and 1.0")
    duty_cycle = get_user_input("  Duty cycle (0 to 1)", 0.5)

duration = get_user_input("  Duration (seconds)", 10)

# Calculate timing parameters
period, high_time, low_time = calculate_timing(frequency, duty_cycle)

# Configuration display
print("\n" + "=" * 70)
print("Configuration")
print("=" * 70)
print(f"Output pin:        {OUTPUT_PIN_NAME}")
print(f"Frequency:         {frequency} Hz")
print(f"Duty cycle:        {duty_cycle * 100:.1f}%")
print(f"Period:            {period:.3f} seconds")
print(f"High time:         {high_time:.3f} seconds")
print(f"Low time:          {low_time:.3f} seconds")
print(f"Duration:          {duration} seconds")
print("=" * 70)


# ==============================================================================
# INITIALIZATION
# ==============================================================================

print("\nInitializing Red Pitaya...")
rp.rp_Init()
rp.rp_DpinSetDirection(OUTPUT_PIN, rp.RP_OUT)
print("Red Pitaya initialized")
print(f"Pin {OUTPUT_PIN_NAME} configured as output")


# ==============================================================================
# PWM GENERATION LOOP
# ==============================================================================

try:
    print(f"\nOutputting a {duty_cycle*100:.1f}% duty cycle PWM at {frequency} Hz on pin {OUTPUT_PIN_NAME}")
    print("Press Ctrl+C to quit\n")

    while True:
        print(f"Generating square wave for {duration} seconds...")
        
        # Generate square wave
        output_square_wave(frequency, duty_cycle, duration)
        
        print("Generation complete")
        
        # Ask user if they want to continue
        user_continue = input("\nContinue generating square waves? (y/n): ").strip().lower()
        if user_continue == 'n':
            break
        
        # Get new parameters
        print("\nEnter new parameters:")
        frequency = get_user_input("  Frequency (Hz)", frequency)
        while frequency <= 0:
            print("  ERROR: Frequency must be greater than 0 Hz")
            frequency = get_user_input("  Frequency (Hz)", frequency)

        duty_cycle = get_user_input("  Duty cycle (0 to 1)", duty_cycle)
        while not 0.0 <= duty_cycle <= 1.0:
            print("  ERROR: Duty cycle must be between 0.0 and 1.0")
            duty_cycle = get_user_input("  Duty cycle (0 to 1)", duty_cycle)

        duration = get_user_input("  Duration (seconds)", duration)
        
        print("\nUpdated configuration:")
        print(f"  Frequency:   {frequency} Hz")
        print(f"  Duty cycle:  {duty_cycle * 100:.1f}%")
        print(f"  Duration:    {duration} seconds")
        
except KeyboardInterrupt:
    print('\n\nKeyboard interrupt detected')


# ==============================================================================
# CLEANUP
# ==============================================================================

print("\nCleaning up...")
rp.rp_DpinSetState(OUTPUT_PIN, rp.RP_LOW)  # Set pin to LOW
rp.rp_Release()  # Release resources
print("Resources released")
