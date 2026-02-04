#!/usr/bin/python3
"""
Red Pitaya Interactive LED Bar Graph Example
=============================================

This example demonstrates an interactive visual LED bar graph using Red Pitaya's
8 built-in LEDs with a graphical user interface. Users can adjust the number of
lit LEDs using a slider control, providing real-time visual feedback both in the
GUI and on the Red Pitaya board's physical LEDs.

Features:
- Interactive GUI with slider control (0-8 LEDs)
- Real-time LED updates as slider moves
- Visual representation in GUI matching physical LEDs
- Percentage display based on number of LEDs lit
- Clean shutdown with proper resource cleanup

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Built-in LEDs (LED0-LED7, no external connections required)

Software Requirements:
- Red Pitaya Python API (rp module)
- tkinter (usually included with Python)

Usage:
    python dig_3_led_inter_bar_graph.py
    
    Use the slider to adjust the number of LEDs from 0 to 8.
    Close the window or press 'Quit' button to exit.

Note:
    This example uses tkinter for the GUI. Make sure you have a display
    environment available (X11, VNC, or local display).

Author: Red Pitaya
Date: January 2026
"""

import tkinter as tk
from tkinter import ttk
import rp


# ==============================================================================
# CONFIGURATION - Set your interactive bar graph parameters here
# ==============================================================================

# GUI window parameters
window_title = "Red Pitaya LED Bar Graph"
window_width = 600
window_height = 400
led_colors = {
    'off': '#2b2b2b',
    'on': '#00ff00'
}

# LED parameters
num_leds = 8                    # Total number of LEDs available
update_interval = 50            # GUI update interval in milliseconds

print("=" * 70)
print("Red Pitaya Interactive LED Bar Graph Configuration")
print("=" * 70)
print(f"Window title:        {window_title}")
print(f"Window size:         {window_width}x{window_height}")
print(f"Number of LEDs:      {num_leds}")
print(f"Update interval:     {update_interval} ms")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya
# ==============================================================================

print("\nInitializing Red Pitaya...")

# Initialize the Red Pitaya interface
rp.rp_Init()
print("Red Pitaya initialized")

# Turn off all LEDs initially
rp.rp_LEDSetState(0b00000000)
print("All LEDs turned off")


# ==============================================================================
# GUI APPLICATION CLASS - Interactive LED control interface
# ==============================================================================

class LEDBarGraphApp:
    """
    Interactive LED bar graph application with GUI control.
    """
    
    def __init__(self, master):
        """
        Initialize the LED bar graph application.
        
        Args:
            master: The tkinter root window
        """
        self.master = master
        self.master.title(window_title)
        self.master.geometry(f"{window_width}x{window_height}")
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # LED state
        self.current_leds = 0
        self.led_array = [rp.RP_LED0, rp.RP_LED1, rp.RP_LED2, rp.RP_LED3,
                          rp.RP_LED4, rp.RP_LED5, rp.RP_LED6, rp.RP_LED7]
        
        # Create GUI elements
        self.create_widgets()
        
        # Initialize LED display
        self.update_leds(0)
        
        print("\nGUI initialized - use slider to control LEDs")
    
    def create_widgets(self):
        """
        Create and layout all GUI widgets.
        """
        # Title label
        title_label = tk.Label(
            self.master,
            text="Red Pitaya LED Bar Graph Controller",
            font=("Arial", 16, "bold"),
            pady=20
        )
        title_label.pack()
        
        # LED visual display frame
        led_frame = tk.Frame(self.master)
        led_frame.pack(pady=20)
        
        # Create visual LED indicators
        self.led_indicators = []
        for i in range(num_leds):
            led_canvas = tk.Canvas(
                led_frame,
                width=50,
                height=50,
                bg='white',
                highlightthickness=1
            )
            led_canvas.pack(side=tk.LEFT, padx=5)
            
            # Draw LED circle
            led = led_canvas.create_oval(
                10, 10, 40, 40,
                fill=led_colors['off'],
                outline='black',
                width=2
            )
            
            # Add LED label
            label = tk.Label(led_frame, text=f"LED{i}")
            
            self.led_indicators.append({
                'canvas': led_canvas,
                'circle': led,
                'label': label
            })
        
        # Position LED labels below circles
        for indicator in self.led_indicators:
            indicator['label'].place(
                x=indicator['canvas'].winfo_x(),
                y=indicator['canvas'].winfo_y() + 55
            )
        
        # Control frame
        control_frame = tk.Frame(self.master)
        control_frame.pack(pady=20, fill=tk.X, padx=50)
        
        # Slider label
        slider_label = tk.Label(
            control_frame,
            text="Number of LEDs:",
            font=("Arial", 12)
        )
        slider_label.pack()
        
        # LED count slider
        self.slider = tk.Scale(
            control_frame,
            from_=0,
            to=num_leds,
            orient=tk.HORIZONTAL,
            length=400,
            command=self.on_slider_change,
            font=("Arial", 10)
        )
        self.slider.pack(pady=10)
        self.slider.set(0)
        
        # Status label
        self.status_label = tk.Label(
            control_frame,
            text="0 LEDs lit (0%)",
            font=("Arial", 12, "bold")
        )
        self.status_label.pack(pady=10)
        
        # Button frame
        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=10)
        
        # Quick set buttons
        tk.Button(
            button_frame,
            text="All OFF",
            command=lambda: self.slider.set(0),
            width=10,
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="50%",
            command=lambda: self.slider.set(4),
            width=10,
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="All ON",
            command=lambda: self.slider.set(8),
            width=10,
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        # Quit button
        quit_button = tk.Button(
            self.master,
            text="Quit",
            command=self.on_closing,
            width=15,
            font=("Arial", 10),
            bg='#ff4444',
            fg='white'
        )
        quit_button.pack(pady=20)
    
    def on_slider_change(self, value):
        """
        Handle slider value changes.
        
        Args:
            value: New slider value (number of LEDs to light)
        """
        led_count = int(value)
        self.update_leds(led_count)
    
    def update_leds(self, count):
        """
        Update both physical LEDs and GUI indicators.
        
        Args:
            count: Number of LEDs to light up (0-8)
        """
        self.current_leds = count
        
        # Update physical LEDs on Red Pitaya
        for i in range(num_leds):
            if i < count:
                rp.rp_DpinSetState(self.led_array[i], rp.RP_HIGH)
            else:
                rp.rp_DpinSetState(self.led_array[i], rp.RP_LOW)
        
        # Update GUI LED indicators
        for i, indicator in enumerate(self.led_indicators):
            color = led_colors['on'] if i < count else led_colors['off']
            indicator['canvas'].itemconfig(indicator['circle'], fill=color)
        
        # Update status label
        percentage = (count / num_leds) * 100
        self.status_label.config(
            text=f"{count} LED{'s' if count != 1 else ''} lit ({percentage:.1f}%)"
        )
        
        print(f"LEDs updated: {count}/{num_leds} lit ({percentage:.1f}%)")
    
    def on_closing(self):
        """
        Handle window closing event with proper cleanup.
        """
        print("\nClosing application...")
        
        # Turn off all LEDs
        print("Turning off all LEDs...")
        for led in self.led_array:
            rp.rp_DpinSetState(led, rp.RP_LOW)
        
        # Release Red Pitaya resources
        print("Releasing Red Pitaya resources...")
        rp.rp_Release()
        
        print("Cleanup complete")
        
        # Close the window
        self.master.destroy()


# ==============================================================================
# MAIN EXECUTION - Run the interactive application
# ==============================================================================

def main():
    """
    Main function to initialize and run the LED bar graph application.
    """
    print("\nStarting interactive LED bar graph application...")
    
    try:
        # Create tkinter root window
        root = tk.Tk()
        
        # Create application instance
        app = LEDBarGraphApp(root)
        
        print("Application running - close window to exit")
        
        # Start the GUI event loop
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt detected (Ctrl+C)")
        
        # Turn off all LEDs
        rp.rp_LEDSetState(0b00000000)
        
        # Release resources
        rp.rp_Release()
        
        print("Resources released - program complete")
    
    except Exception as e:
        print(f"\nERROR: {e}")
        
        # Ensure cleanup on error
        try:
            rp.rp_LEDSetState(0b00000000)
            rp.rp_Release()
        except:
            pass
        
        print("Emergency cleanup complete")


if __name__ == "__main__":
    main()
