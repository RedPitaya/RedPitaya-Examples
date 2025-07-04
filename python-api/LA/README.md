**README - Configuration Parameters Guide**

This document describes the available configuration parameters for the system.

**CAN settings**
 
**Configuration:**
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


**I2C settings**

**Configuration:**
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

**SPI settings**

**Configuration:**
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

**UART settings**

Here's the consolidated README for UART configuration in a continuous text format:

---

**README - UART Configuration Parameters Guide**

**Configuration:**
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