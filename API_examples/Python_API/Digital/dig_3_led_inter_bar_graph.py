#!/usr/bin/python3
"""
Red Pitaya Interactive LED Bar Graph Example
=============================================

This example demonstrates interactive real-time control of Red Pitaya's 8 built-in
LEDs as a bar graph, using single-keypress input — no Enter key required.

Press '+' or the right arrow to add one LED, '-' or the left arrow to remove one,
and 'q' to quit. The terminal shows an ASCII bar that mirrors the physical LEDs.

Features:
- Single-keypress control (no Enter required)
- Real-time ASCII bar in terminal mirrors physical LEDs
- '+' / right arrow: increase LED count
- '-' / left arrow:  decrease LED count
- 'q' / Ctrl+C: quit

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Built-in LEDs (LED0-LED7, no external connections required)

Software Requirements:
- Red Pitaya Python API (rp module)
- Standard Linux terminal (tty/termios — available on Red Pitaya OS)

Usage:
    python dig_3_led_inter_bar_graph.py

Note:
    Raw terminal mode is used to capture single keypresses. The terminal is
    fully restored to its original state on exit, even if the program crashes.

Author: Red Pitaya
Date: May 2026
"""

import sys
import tty
import termios
import rp



# ==============================================================================
# CONFIGURATION
# ==============================================================================

NUM_LEDS = 8
led_array = [rp.RP_LED0, rp.RP_LED1, rp.RP_LED2, rp.RP_LED3,
             rp.RP_LED4, rp.RP_LED5, rp.RP_LED6, rp.RP_LED7]


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def read_single_key():
    """
    Read a single keypress from stdin without requiring Enter.
    Handles regular characters and 3-byte ANSI escape sequences (arrow keys).

    Returns:
        str: The key pressed. Arrow keys are returned as 'RIGHT' or 'LEFT'.
             All other keys are returned as their character.
    """
    ch = sys.stdin.read(1)
    if ch == '\x1b':                        # Start of an ANSI escape sequence
        ch2 = sys.stdin.read(1)
        if ch2 == '[':
            ch3 = sys.stdin.read(1)
            if ch3 == 'C':
                return 'RIGHT'              # Right arrow
            if ch3 == 'D':
                return 'LEFT'              # Left arrow
        return '\x1b'                       # Lone Escape key
    return ch


def set_leds(count):
    """
    Light up the first `count` LEDs and turn off the rest.

    Args:
        count (int): Number of LEDs to light (0-8).
    """
    for i in range(NUM_LEDS):
        state = rp.RP_HIGH if i < count else rp.RP_LOW
        rp.rp_DpinSetState(led_array[i], state)


def print_bar(count):
    """
    Print an ASCII bar to the terminal representing the current LED state.
    Overwrites the previous line using a carriage return.

    Args:
        count (int): Number of LEDs currently lit.
    """
    filled = '\u2588' * count               # Full block characters for lit LEDs
    empty  = '\u2591' * (NUM_LEDS - count)  # Light shade characters for unlit LEDs
    percent = (count / NUM_LEDS) * 100
    bar = f"\r  LEDs: [{filled}{empty}]  {count}/{NUM_LEDS}  ({percent:.0f}%)   "
    sys.stdout.write(bar)
    sys.stdout.flush()


# ==============================================================================
# INITIALIZATION
# ==============================================================================

print("=" * 70)
print("Red Pitaya Interactive LED Bar Graph")
print("=" * 70)
print("  '+'  or right arrow : increase LED count")
print("  '-'  or left arrow  : decrease LED count")
print("  'q'  or Ctrl+C      : quit")
print("=" * 70)

rp.rp_Init()
rp.rp_LEDSetState(0b00000000)
print("\nRed Pitaya initialized — all LEDs off\n")


# ==============================================================================
# INTERACTIVE CONTROL LOOP
# ==============================================================================

current_count = 0
set_leds(current_count)
print_bar(current_count)

# Save terminal settings so we can restore them on exit
original_term_settings = termios.tcgetattr(sys.stdin)

try:
    tty.setraw(sys.stdin.fileno())          # Switch to raw mode: no echo, no line buffering

    while True:
        key = read_single_key()

        if key in ('+', 'RIGHT') and current_count < NUM_LEDS:
            current_count += 1
        elif key in ('-', 'LEFT') and current_count > 0:
            current_count -= 1
        elif key in ('q', 'Q', '\x03'):     # 'q', 'Q', or Ctrl+C
            break

        set_leds(current_count)
        print_bar(current_count)

finally:
    # Always restore the terminal before exiting, even on exception
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_term_settings)


# ==============================================================================
# CLEANUP
# ==============================================================================

print("\n\nExiting...")
rp.rp_LEDSetState(0b00000000)
rp.rp_Release()
print("All LEDs off — resources released")
