#!/usr/bin/python3

from rp_arb import *
import numpy as np

def example_list_files():
    """Example: List all loaded ARB files"""
    print("=== Listing ARB Files ===")

    rp_ARBInit()
    rp_ARBLoadFiles()

    count = rp_ARBGetCount()[1]
    print(f"Found {count} files:")

    for i in range(count):
        name = rp_ARBGetName(i)[1]
        color = rp_ARBGetColor(i)[1]
        filename = rp_ARBGetFileName(i)[1]
        print(f"  {i}: {name} (color: {color:#08x}, file: {filename})")

def example_get_signal_by_name():
    """Example: Get signal data by name"""
    print("\n=== Getting Signal by Name ===")

    rp_ARBInit()
    rp_ARBLoadFiles()

    # Create buffer
    buffer = np.zeros(1024 * 16, dtype=np.float32)

    # Get signal by name (replace with actual signal name from your files)
    signal_name = "example_signal"  # Change this to match your signal name
    result = rp_ARBGetSignalByNameNP(signal_name, buffer)

    if result[0] == RP_ARB_FILE_OK:
        print(f"Signal '{signal_name}' loaded successfully")
        print(f"First 10 points: {buffer[:10]}")
    else:
        print(f"Error loading signal '{signal_name}': code {result[0]}")

def example_generate_files():
    """Example: Generate CSV and COE files"""
    print("\n=== Generating Output Files ===")

    rp_ARBInit()
    rp_ARBLoadFiles()

    # Generate CSV file
    rp_ARBGenFileCSV("output_signal.csv")
    print("Generated CSV file: output_signal.csv")

    # Generate COE file
    rp_ARBGenFileCOE("output_signal.coe")
    print("Generated COE file: output_signal.coe")

def example_rename_file():
    """Example: Rename ARB file"""
    print("\n=== Renaming ARB File ===")

    rp_ARBInit()
    rp_ARBLoadFiles()

    count = rp_ARBGetCount()[1]
    if count > 0:
        old_name = rp_ARBGetName(0)[1]
        print(f"Original name: {old_name}")

        # Rename first file
        rp_ARBRenameFile(0, "example_signal")

        new_name = rp_ARBGetName(0)[1]
        print(f"New name: {new_name}")

def example_load_to_fpga():
    """Example: Load signal to FPGA"""
    print("\n=== Loading Signal to FPGA ===")

    rp_ARBInit()
    rp_ARBLoadFiles()

    count = rp_ARBGetCount()[1]
    if count > 0:
        signal_name = rp_ARBGetName(0)[1]

        # Load to FPGA channel 0
        result = rp_ARBLoadToFPGA(0, signal_name)

        if result == RP_ARB_FILE_OK:
            print(f"Signal '{signal_name}' loaded to FPGA channel 0")
        else:
            print(f"Error loading to FPGA: code {result}")

def example_check_signal_valid():
    """Example: Check if signal is valid"""
    print("\n=== Checking Signal Validity ===")

    rp_ARBInit()
    rp_ARBLoadFiles()

    count = rp_ARBGetCount()[1]
    for i in range(count):
        signal_name = rp_ARBGetName(i)[1]
        valid = rp_ARBIsValid(signal_name)[1]
        status = "VALID" if valid else "INVALID"
        print(f"Signal '{signal_name}': {status}")

def example_multiple_signals():
    """Example: Work with multiple signals"""
    print("\n=== Working with Multiple Signals ===")

    rp_ARBInit()
    rp_ARBLoadFiles()

    count = rp_ARBGetCount()[1]
    buffer = np.zeros(1024 * 16, dtype=np.float32)

    for i in range(min(count, 30)):  # Process first 3 signals
        name = rp_ARBGetName(i)[1]
        rp_ARBGetSignalNP(i, buffer)

        print(f"Signal {i} ({name}):")
        print(f"  Min: {buffer.min():.4f}, Max: {buffer.max():.4f}")
        print(f"  Mean: {buffer.mean():.4f}, Std: {buffer.std():.4f}")

def example_change_colors():
    """Example: Change signal colors"""
    print("\n=== Changing Signal Colors ===")

    rp_ARBInit()
    rp_ARBLoadFiles()

    count = rp_ARBGetCount()[1]

    # Define some colors (RGB format)
    colors = [0xFF0000, 0x00FF00, 0x0000FF, 0xFFFF00, 0xFF00FF]

    for i in range(count):
        if i < len(colors):
            rp_ARBSetColor(i, colors[i])
            new_color = rp_ARBGetColor(i)[1]
            name = rp_ARBGetName(i)[1]
            print(f"Signal '{name}' color set to: {new_color:#08x}")

# Run all examples
if __name__ == "__main__":
    example_list_files()
    example_get_signal_by_name()
    example_generate_files()
    example_rename_file()
    example_load_to_fpga()
    example_check_signal_valid()
    example_multiple_signals()
    example_change_colors()