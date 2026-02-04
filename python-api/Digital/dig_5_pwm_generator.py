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
- Data capture for waveform visualization
- Matplotlib plot of generated signal
- Keyboard interrupt handling for clean exit

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Optional: LED, oscilloscope, or logic analyzer to observe output

GPIO Pin Used:
- DIO1_P (Digital I/O pin 1 Positive) - Square wave output

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- Matplotlib library

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
import numpy as np
import matplotlib.pyplot as plt


# ==============================================================================
# CONSTANTS
# ==============================================================================

OUTPUT_PIN = rp.RP_DIO1_P       # GPIO pin for PWM output
OUTPUT_PIN_NAME = "DIO1_P"      # Pin name for display
SAMPLING_RATE = 1000            # Samples per second for data capture


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
    return float(user_input) if user_input else default 


def calculate_timing(frequency, duty_cycle):
    """
    Calculate timing parameters for PWM signal.
    
    Args:
        frequency (float): PWM frequency in Hz
        duty_cycle (float): Duty cycle (0.0 to 1.0)
        
    Returns:
        tuple: (period, high_time, low_time) in seconds
    """
    period = 1.0 / frequency
    high_time = period * duty_cycle
    low_time = period * (1 - duty_cycle)
    return period, high_time, low_time


def output_square_wave(frequency, duty_cycle, duration, input_data):
    """
    Generate a square wave output on GPIO pin with data capture.
    
    Args:
        frequency (float): PWM frequency in Hz
        duty_cycle (float): Duty cycle (0.0 to 1.0)
        duration (float): Duration in seconds
        input_data (np.array): Array to store captured data
        
    Returns:
        None
    """
    period, high_time, low_time = calculate_timing(frequency, duty_cycle)
    sample_interval = 1.0 / SAMPLING_RATE
    num_high_samples = int(high_time * SAMPLING_RATE)
    num_low_samples = int(low_time * SAMPLING_RATE)
    
    start_time = time.time()
    sample_index = 0
    max_samples = len(input_data)
    
    # Generate square wave for specified duration
    while (time.time() - start_time) < duration and sample_index < max_samples:
        # HIGH state
        rp.rp_DpinSetState(OUTPUT_PIN, rp.RP_HIGH)
        for _ in range(num_high_samples):
            if sample_index >= max_samples:
                break
            input_data[sample_index] = 1
            sample_index += 1
            time.sleep(sample_interval)

        # LOW state
        rp.rp_DpinSetState(OUTPUT_PIN, rp.RP_LOW)
        for _ in range(num_low_samples):
            if sample_index >= max_samples:
                break
            input_data[sample_index] = 0
            sample_index += 1
            time.sleep(sample_interval)


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

print("=" * 70)
print("Red Pitaya - PWM Square Wave Generator")
print("=" * 70)

# Get initial user-defined parameters
print("\nEnter PWM parameters:")
frequency = get_user_input("  Frequency (Hz)", 1)
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
print(f"Sampling rate:     {SAMPLING_RATE} Hz")
print("=" * 70)


# ==============================================================================
# INITIALIZATION
# ==============================================================================

print("\nInitializing Red Pitaya...")
rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# PWM GENERATION LOOP
# ==============================================================================

# Initialize variables for visualization (store last generated waveform)
last_time_data = None
last_input_data = None
last_frequency = frequency
last_duty_cycle = duty_cycle

try:
    print(f"\nOutputting a {duty_cycle*100:.1f}% duty cycle PWM at {frequency} Hz on pin {OUTPUT_PIN_NAME}")
    print("Press Ctrl+C to quit\n")

    while True:
        # Allocate data capture arrays
        num_samples = int(SAMPLING_RATE * duration)
        time_data = np.linspace(0, duration, num_samples)
        input_data = np.zeros(num_samples)
        
        print(f"Generating square wave for {duration} seconds...")
        
        # Generate square wave
        output_square_wave(frequency, duty_cycle, duration, input_data)
        
        print("Generation complete")
        
        # Store data for visualization
        last_time_data = time_data
        last_input_data = input_data
        last_frequency = frequency
        last_duty_cycle = duty_cycle
        
        # Ask user if they want to continue
        user_continue = input("\nContinue generating square waves? (y/n): ").strip().lower()
        if user_continue == 'n':
            break
        
        # Get new parameters
        print("\nEnter new parameters:")
        frequency = get_user_input("  Frequency (Hz)", frequency)
        duty_cycle = get_user_input("  Duty cycle (0 to 1)", duty_cycle)
        duration = get_user_input("  Duration (seconds)", duration)
        
        print(f"\nUpdated configuration:")
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


# ==============================================================================
# VISUALIZATION - Plot Generated Waveform
# ==============================================================================

# Only plot if we have captured data
if last_time_data is not None and last_input_data is not None:
    print("\nGenerating waveform plot...")
    
    # Calculate timing for statistics
    period, high_time, low_time = calculate_timing(last_frequency, last_duty_cycle)
    
    # Create visualization
    plt.figure(figsize=(12, 5))
    plt.step(last_time_data, last_input_data, where='post',
             label=f"PWM Signal ({last_duty_cycle*100:.1f}% duty cycle)", linewidth=2, color='blue')
    
    plt.title(f"Square Wave Output from Red Pitaya - {last_frequency} Hz PWM", 
              fontsize=14, fontweight='bold')
    plt.xlabel("Time (seconds)", fontsize=12)
    plt.ylabel("Digital State", fontsize=12)
    plt.yticks([0, 1], ['LOW (0V)', 'HIGH (3.3V)'])
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)
    plt.ylim(-0.1, 1.1)
    plt.xlim(0, last_time_data[-1])
    
    # Add statistics text box
    stats_text = f"Period: {period:.3f}s\nHigh: {high_time:.3f}s\nLow: {low_time:.3f}s"
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
             fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.show()
else:
    print("\nNo waveform data to visualize")

print("Program complete")      