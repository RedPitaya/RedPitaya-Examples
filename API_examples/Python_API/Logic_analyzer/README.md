# Red Pitaya Logic Analyzer - Python API Examples

## Overview

This folder contains comprehensive examples demonstrating the use of Red Pitaya's Logic Analyzer functionality through the Python API. The Logic Analyzer enables protocol decoding for common communication interfaces including UART, SPI, I2C, and CAN bus protocols.

The examples are organized into three categories:
- **FPGA-based decoding with loopback**: Capture and decode signals directly from Red Pitaya hardware
- **External signal decoding**: Decode signals from external devices connected to digital inputs
- **File-based decoding**: Decode previously captured binary data files
- **Settings management**: Export and modify decoder configuration files

## Hardware Requirements

- Red Pitaya board (STEMlab 125-14 or compatible model)
- Logic Analyzer FPGA image must be loaded
- For loopback examples: No external connections required
- For external signal examples: Connect protocol signals to DIN0-DIN7 pins
- Operating System: Red Pitaya OS 2.00 or higher

## Software Requirements

- Red Pitaya Python API (`rp` module)
- Red Pitaya Logic Analyzer module (`rp_la`)
- Logic Analyzer application or FPGA image loaded

## Example Files

### FPGA Loopback Examples (fpga_decode_*.py)
These examples generate signals internally and decode them using the FPGA-based decoder:

- **fpga_decode_1_can_loop.py** - CAN bus protocol (Note: CAN loopback not supported due to hardware limitations)
- **fpga_decode_2_i2c_loop.py** - I2C protocol with EEPROM communication loopback
- **fpga_decode_3_spi_loop.py** - SPI protocol with full-duplex loopback
- **fpga_decode_4_uart_loop.py** - UART protocol with TX/RX loopback

### External Signal Decoding (la_decode_*.py)
These examples decode signals from external devices connected to the digital inputs:

- **la_decode_1_can_fpga.py** - Decode CAN bus signals from external sources
- **la_decode_2_i2c_fpga.py** - Decode I2C communication from external devices
- **la_decode_3_spi_fpga.py** - Decode SPI transactions from external sources
- **la_decode_4_uart_fpga.py** - Decode UART communication from external devices

### File-Based Decoding (file_decode_*.py)
These examples decode protocol data from pre-captured binary dump files:

- **file_decode_1_can.py** - Decode CAN data from dump_can.bin
- **file_decode_2_i2c.py** - Decode I2C data from dump_i2c.bin
- **file_decode_3_spi.py** - Decode SPI data from dump_spi.bin
- **file_decode_4_uart.py** - Decode UART data from dump_uart.bin

### Settings Management
- **la_settings_save_file.py** - Export default decoder settings to JSON files (creates configuration templates)
- **la_settings_modify_file.py** - Modify and save custom decoder configurations

## Quick Start

### 1. Load Logic Analyzer FPGA
Before running any examples, ensure the Logic Analyzer FPGA image is loaded:
```bash
# Option 1: Open the Logic Analyzer web application
# Navigate to http://rp-xxxxxx.local/bazaar?start=la

# Option 2: Use the CLI to load the FPGA
# (Method depends on your Red Pitaya setup)
```

### 2. Run an Example
```bash
# SSH into your Red Pitaya
ssh root@rp-xxxxxx.local

# Navigate to the examples directory
cd /path/to/Logic_analyzer/

# Run an example
python3 la_decode_4_uart_fpga.py
```

### 3. Connect External Signals (for la_decode_*.py examples)
Connect your protocol signals to the appropriate DIN pins:
- **UART**: Connect RX to DIN0 (TX optional on DIN1)
- **SPI**: Connect CLK to DIN0, MOSI to DIN1, CS to DIN2, MISO to DIN3 (optional)
- **I2C**: Connect SCL to DIN0, SDA to DIN1
- **CAN**: Connect CAN RX to DIN0

## Configuration Files

The following JSON configuration files define decoder parameters:
- **settings_uart.json** - UART decoder configuration
- **settings_spi.json** - SPI decoder configuration
- **settings_i2c.json** - I2C decoder configuration
- **settings_can.json** - CAN decoder configuration

You can create these files using `la_settings_save_file.py` or modify them manually following the parameter guide below.

## Binary Dump Files

Pre-captured binary data files for offline decoding:
- **dump_uart.bin** - Sample UART capture
- **dump_spi.bin** - Sample SPI capture
- **dump_i2c.bin** - Sample I2C capture
- **dump_can.bin** - Sample CAN capture

---

## Configuration Parameters Guide

This section describes the available configuration parameters for each protocol decoder. These settings are the latest version and should be used when creating or modifying decoder configurations.

### CAN Settings
 
**Default Configuration:**
```json
{
	"acq_speed" : 100000000,
	"fast_bitrate" : 2000000,
	"invert_bit" : "No",
	"nominal_bitrate" : 1000000,
	"rx" : "DIN0",
	"sample_point" : 80
}
```

**Parameter Details:**

1. **acq_speed** - Specifies the acquisition speed in Hertz (Hz). Must be a positive integer value (e.g., 100000000 for 100 MHz).

2. **fast_bitrate** - Defines the fast bitrate in bits per second (bps). Must be a positive integer (e.g., 2000000 for 2 Mbps).

3. **invert_bit** - Determines whether to invert the bit signal. Acceptable values are from the InvertBit enum:
   - "No" (default) - No inversion
   - "Yes" - Signal will be inverted

4. **nominal_bitrate** - Sets the nominal bitrate in bps. Must be a positive integer (e.g., 1000000 for 1 Mbps).

5. **rx** - Specifies the receive line (input channel) to use. Valid options from the Lines enum:
   - "None" - No line selected
   - "DIN0" - Digital Input 0
   - "DIN1" - Digital Input 1
   - "DIN2" - Digital Input 2
   - "DIN3" - Digital Input 3
   - "DIN4" - Digital Input 4
   - "DIN5" - Digital Input 5
   - "DIN6" - Digital Input 6
   - "DIN7" - Digital Input 7

6. **sample_point** - Sets the sample point percentage. Must be an integer between 0 and 100 (e.g., 80 for 80%).

**CAN Configuration Example:**
```python
# Setting all CAN parameters
la.setDecoderSettingsString("can1", "rx", "DIN0")
la.setDecoderSettingsUInt("can1", "nominal_bitrate", 500000)
la.setDecoderSettingsUInt("can1", "fast_bitrate", 2000000)
la.setDecoderSettingsUInt("can1", "acq_speed", 100000000)
la.setDecoderSettingsString("can1", "invert_bit", "No")
la.setDecoderSettingsFloat("can1", "sample_point", 75.0)
```


### I2C Settings

**Default Configuration:**
```json
{
	"acq_speed" : 4000000,
	"address_format" : "Shifted",
	"invert_bit" : "No",
	"scl" : "DIN0",
	"sda" : "DIN1"
}
```

**Parameter Details:**

1. **acq_speed** - Specifies the acquisition speed in Hertz (Hz) for signal sampling. Must be a positive integer value (e.g., 4000000 for 4 MHz). This affects the timing resolution of the I2C signal capture.

2. **address_format** - Determines how I2C device addresses are interpreted. Acceptable values are from the AddressFormat enum:
   - "Shifted" (default) - Address is treated as 7-bit value shifted left by 1 bit (common in most implementations)
   - "Unshifted" - Address is treated as raw 8-bit value (including R/W bit)

3. **invert_bit** - Controls whether the signal polarity should be inverted. Acceptable values are from the InvertBit enum:
   - "No" (default) - Normal signal polarity
   - "Yes" - Inverted signal polarity

4. **scl** - Specifies the digital input line to use for the Serial Clock (SCL) signal. Valid options from the Lines enum:
   - "None" - No line selected
   - "DIN0" - Digital Input 0
   - "DIN1" - Digital Input 1
   - "DIN2" - Digital Input 2
   - Up to "DIN7" - Digital Input 7

5. **sda** - Specifies the digital input line to use for the Serial Data (SDA) signal. Uses the same Lines enum values as scl.

**I2C Configuration Example:**
```python
# Setting all I2C parameters
la.setDecoderSettingsString("i2c1", "scl", "DIN0")
la.setDecoderSettingsString("i2c1", "sda", "DIN1")
la.setDecoderSettingsUInt("i2c1", "acq_speed", 4000000)
la.setDecoderSettingsString("i2c1", "address_format", "Shifted")
la.setDecoderSettingsString("i2c1", "invert_bit", "No")
```

### SPI Settings

**Default Configuration:**
```json
{
	"acq_speed": 0,
	"bit_order": "MsbFirst",
	"clk": "DIN0",
	"cpha": 0,
	"cpol": 0,
	"cs": "DIN2",
	"cs_polarity": "ActiveLow",
	"invert_bit": "No",
	"miso": "None",
	"mosi": "DIN1",
	"word_size": 8
}
```

**Parameter Details:**

1. **acq_speed** - Acquisition speed in Hertz (Hz) for signal sampling. Value 0 means automatic speed selection. Must be a non-negative integer.

2. **bit_order** - Specifies bit transmission order. Values from BitOrder enum:
   - "MsbFirst" (default) - Most significant bit first
   - "LsbFirst" - Least significant bit first

3. **clk** - Clock line (SCLK) selection. Values from Lines enum:
   - "DIN0" through "DIN7" - Digital input lines

4. **cpha** - Clock phase (0 or 1):
   - 0: Data sampled on leading clock edge
   - 1: Data sampled on trailing clock edge

5. **cpol** - Clock polarity (0 or 1):
   - 0: Clock idle low (default)
   - 1: Clock idle high

6. **cs** - Chip select line. Uses same Lines enum values as clk.

7. **cs_polarity** - Chip select active state. Values from CsPolarity enum:
   - "ActiveLow" (default) - CS active when low
   - "ActiveHigh" - CS active when high

8. **invert_bit** - Signal inversion control. Values from InvertBit enum:
   - "No" (default) - Normal polarity
   - "Yes" - Inverted polarity

9. **miso** - Master Input Slave Output line. Uses Lines enum.

10. **mosi** - Master Output Slave Input line. Uses Lines enum.

11. **word_size** - Data word size in bits (default 8).

**SPI Mode Combinations:**
The combination of CPOL and CPHA defines the SPI mode:
- Mode 0: CPOL=0, CPHA=0
- Mode 1: CPOL=0, CPHA=1
- Mode 2: CPOL=1, CPHA=0
- Mode 3: CPOL=1, CPHA=1

**SPI Configuration Example:**
```python
# Configure SPI Mode 0
la.setDecoderSettingsString("spi1", "clk", "DIN0")
la.setDecoderSettingsString("spi1", "mosi", "DIN1")
la.setDecoderSettingsString("spi1", "miso", "DIN2")
la.setDecoderSettingsString("spi1", "cs", "DIN3")
la.setDecoderSettingsUInt("spi1", "cpol", 0)
la.setDecoderSettingsUInt("spi1", "cpha", 0)
la.setDecoderSettingsString("spi1", "bit_order", "MsbFirst")
la.setDecoderSettingsString("spi1", "cs_polarity", "ActiveLow")
la.setDecoderSettingsUInt("spi1", "word_size", 8)
```

### UART Settings

**Default Configuration:**
```json
{
	"acq_speed": 1000000,
	"baudrate": 115200,
	"bitOrder": "LsbFirst",
	"invert": "No",
	"num_data_bits": "Bits8",
	"num_stop_bits": "Stop_Bit_10",
	"parity": "None",
	"rx": "DIN0",
	"tx": "None"
}
```

**Parameter Details:**

1. **acq_speed** - Acquisition speed in Hertz (Hz) for signal sampling. Must be significantly higher than baudrate (default 1MHz). Recommended minimum is 4x baudrate.

2. **baudrate** - Communication speed in bits per second (default 115200). Common values include 9600, 19200, 38400, 57600, 115200.

3. **bitOrder** - Bit transmission order. Values from UartBitOrder enum:
   - "LsbFirst" (default) - Least significant bit first (standard for UART)
   - "MsbFirst" - Most significant bit first

4. **invert** - Signal polarity control. Values from InvertBit enum:
   - "No" (default) - Normal polarity
   - "Yes" - Inverted signal (idle high instead of idle low)

5. **num_data_bits** - Number of data bits per character. Values from NumDataBits enum:
   - "Bits5" - 5 data bits
   - "Bits6" - 6 data bits
   - "Bits7" - 7 data bits
   - "Bits8" (default) - 8 data bits
   - "Bits9" - 9 data bits

6. **num_stop_bits** - Stop bits configuration. Values from NumStopBits enum:
   - "Stop_Bit_No" - No stop bit
   - "Stop_Bit_05" - 0.5 stop bits
   - "Stop_Bit_10" (default) - 1 stop bit
   - "Stop_Bit_15" - 1.5 stop bits
   - "Stop_Bit_20" - 2 stop bits

7. **parity** - Parity bit configuration. Values from Parity enum:
   - "None" (default) - No parity bit
   - "Even" - Even parity
   - "Odd" - Odd parity
   - "Always_0" - Parity bit always 0
   - "Always_1" - Parity bit always 1

8. **rx** - Receive line selection. Values from Lines enum:
   - "None" - No receive line
   - "DIN0" through "DIN7" - Digital input lines

9. **tx** - Transmit line selection. Uses same Lines enum values as rx (default "None").

**UART Configuration Example:**
```python
# Configure UART 8N1 (8 data bits, no parity, 1 stop bit)
la.setDecoderSettingsString("uart1", "rx", "DIN0")
la.setDecoderSettingsUInt("uart1", "baudrate", 115200)
la.setDecoderSettingsString("uart1", "num_data_bits", "Bits8")
la.setDecoderSettingsString("uart1", "parity", "None")
la.setDecoderSettingsString("uart1", "num_stop_bits", "Stop_Bit_10")
la.setDecoderSettingsString("uart1", "bitOrder", "LsbFirst")
la.setDecoderSettingsString("uart1", "invert", "No")
la.setDecoderSettingsUInt("uart1", "acq_speed", 1000000)
```

---

## Common Usage Patterns

### Exporting Decoder Settings
To create backup configuration files or templates:
```bash
python3 la_settings_save_file.py
```
This generates `settings_uart.json`, `settings_spi.json`, `settings_i2c.json`, and `settings_can.json`.

### Modifying Decoder Settings
To customize decoder parameters:
```bash
python3 la_settings_modify_file.py
```
This example shows how to programmatically modify settings such as baud rates, clock speeds, and pin assignments.

### Decoding External Signals
1. Connect your device to the appropriate DIN pins
2. Run the corresponding decoder example:
```bash
python3 la_decode_4_uart_fpga.py  # For UART
python3 la_decode_3_spi_fpga.py   # For SPI
python3 la_decode_2_i2c_fpga.py   # For I2C
python3 la_decode_1_can_fpga.py   # For CAN
```

### Decoding from Files
To decode previously captured data:
```bash
python3 file_decode_4_uart.py  # Decodes dump_uart.bin
```

## Troubleshooting

### Logic Analyzer FPGA Not Loaded
**Error**: `Failed to initialize FPGA`
**Solution**: Open the Logic Analyzer web application at `rp-xxxxxx.local/la_pro/?type=run` or load the FPGA image manually.

### No Data Captured
**Issue**: Decoder reports timeout or no data
**Solutions**:
- Verify signal connections to correct DIN pins
- Check signal voltage levels (must be 3.3V logic compatible)
- Ensure acquisition speed is appropriate for signal frequency
- Confirm protocol parameters match your device settings

### Incorrect Decoding
**Issue**: Data appears corrupted or incorrectly decoded
**Solutions**:
- Verify decoder settings match the protocol configuration (baud rate, clock polarity, etc.)
- Check signal quality and grounding
- Ensure acquisition speed is sufficiently high (typically 4-10x the signal frequency)
- Verify correct pin assignments in configuration

### Python Import Errors
**Error**: `ModuleNotFoundError: No module named 'rp_la'`
**Solution**: Ensure the Red Pitaya OS is up to date and that the programs are executed inside Red Pitaya Linux terminal.

## Digital Input Pin Reference

Red Pitaya digital input pins (Extension connector E2):
- **DIN0** - DIO0_P - Pin 3 (3.3V LVTTL)
- **DIN1** - DIO1_P - Pin 5
- **DIN2** - DIO2_P - Pin 7
- **DIN3** - DIO3_P - Pin 9
- **DIN4** - DIO4_P - Pin 11
- **DIN5** - DIO5_P - Pin 13
- **DIN6** - DIO6_P - Pin 15
- **DIN7** - DIO7_P - Pin 17

**Important**: 
- All digital inputs are 3.3V logic compatible
- Maximum input voltage: 3.3V
- Do not exceed 3.3V to avoid damage to the board
- Ground reference: Pin 25, 26 (GND)

## Additional Resources

- [Red Pitaya Documentation](https://redpitaya.readthedocs.io/)
- [Logic Analyzer Web Application Guide](https://redpitaya.readthedocs.io/en/latest/appsFeatures/applications/logic_analyzer.html)
- [Python API Reference](https://redpitaya.readthedocs.io/en/latest/appsFeatures/remoteControl/python.html)
- [Hardware Specifications](https://redpitaya.readthedocs.io/en/latest/developerGuide/hardware.html)

## Contributing

If you find issues or have improvements for these examples, please contribute to the Red Pitaya repository.

## License

These examples are part of the Red Pitaya project and follow the same license terms.

---

**Last Updated**: May 2026
**Author**: Red Pitaya Team