## Protocol Settings

### CAN Protocol Settings

**Configuration:**
```json
{
    "acq_speed": 100000000,
    "fast_bitrate": 2000000,
    "invert_bit": "No",
    "nominal_bitrate": 1000000,
    "rx": "DIN0",
    "sample_point": 80
}
```

**Parameter Details:**

1. **acq_speed** - Specifies the acquisition speed in Hertz (Hz). Must be a positive integer value (e.g., 100000000 for 100 MHz).

2. **fast_bitrate** - Defines the fast bitrate in bits per second (bps). Must be a positive integer (e.g., 2000000 for 2 Mbps).

3. **invert_bit** - Determines whether to invert the bit signal. Acceptable values from the InvertBit enum:
   - "No" (default) - No inversion
   - "Yes" - Signal will be inverted

4. **nominal_bitrate** - Sets the nominal bitrate in bps. Must be a positive integer (e.g., 1000000 for 1 Mbps).

5. **rx** - Specifies the receive line (input channel) to use. Valid options from the Lines enum:
   - "None" - No line selected
   - "DIN0" through "DIN7" - Digital Input 0-7

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

### I2C Protocol Settings

**Configuration:**
```json
{
    "acq_speed": 4000000,
    "address_format": "Shifted",
    "invert_bit": "No",
    "scl": "DIN0",
    "sda": "DIN1"
}
```

**Parameter Details:**

1. **acq_speed** - Specifies the acquisition speed in Hertz (Hz) for signal sampling. Must be a positive integer value (e.g., 4000000 for 4 MHz). This affects the timing resolution of the I2C signal capture.

2. **address_format** - Determines how I2C device addresses are interpreted. Acceptable values from the AddressFormat enum:
   - "Shifted" (default) - Address treated as 7-bit value shifted left by 1 bit
   - "Unshifted" - Address treated as raw 8-bit value (including R/W bit)

3. **invert_bit** - Controls whether the signal polarity should be inverted. Values from InvertBit enum:
   - "No" (default) - Normal signal polarity
   - "Yes" - Inverted signal polarity

4. **scl** - Specifies the digital input line for the Serial Clock (SCL) signal. Values from Lines enum: "None" or "DIN0" through "DIN7"

5. **sda** - Specifies the digital input line for the Serial Data (SDA) signal. Same Lines enum values as scl.

**I2C Configuration Example:**
```python
# Setting all I2C parameters
la.setDecoderSettingsString("i2c1", "scl", "DIN0")
la.setDecoderSettingsString("i2c1", "sda", "DIN1")
la.setDecoderSettingsUInt("i2c1", "acq_speed", 4000000)
la.setDecoderSettingsString("i2c1", "address_format", "Shifted")
la.setDecoderSettingsString("i2c1", "invert_bit", "No")
```

### SPI Protocol Settings

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

3. **clk** - Clock line (SCLK) selection. Values from Lines enum: "DIN0" through "DIN7"

4. **cpha** - Clock phase (0 or 1):
   - 0: Data sampled on leading clock edge
   - 1: Data sampled on trailing clock edge

5. **cpol** - Clock polarity (0 or 1):
   - 0: Clock idle low (default)
   - 1: Clock idle high

6. **cs** - Chip select line. Same Lines enum values

7. **cs_polarity** - Chip select active state. Values from CsPolarity enum:
   - "ActiveLow" (default) - CS active when low
   - "ActiveHigh" - CS active when high

8. **invert_bit** - Signal inversion control. Values from InvertBit enum

9. **miso** - Master Input Slave Output line. Lines enum values

10. **mosi** - Master Output Slave Input line. Lines enum values

11. **word_size** - Data word size in bits (default 8)

**SPI Mode Combinations:**
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

### UART Protocol Settings

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

2. **baudrate** - Communication speed in bits per second (default 115200). Common values: 9600, 19200, 38400, 57600, 115200.

3. **bitOrder** - Bit transmission order. Values from UartBitOrder enum:
   - "LsbFirst" (default) - Least significant bit first (standard for UART)
   - "MsbFirst" - Most significant bit first

4. **invert** - Signal polarity control. Values from InvertBit enum:
   - "No" (default) - Normal polarity
   - "Yes" - Inverted signal (idle high instead of idle low)

5. **num_data_bits** - Number of data bits per character. Values from NumDataBits enum:
   - "Bits5" through "Bits9" (default "Bits8")

6. **num_stop_bits** - Stop bits configuration. Values from NumStopBits enum:
   - "Stop_Bit_No", "Stop_Bit_05", "Stop_Bit_10" (default), "Stop_Bit_15", "Stop_Bit_20"

7. **parity** - Parity bit configuration. Values from Parity enum:
   - "None" (default), "Even", "Odd", "Always_0", "Always_1"

8. **rx** - Receive line selection. Values from Lines enum

9. **tx** - Transmit line selection. Same Lines enum values (default "None")

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