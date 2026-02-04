# Red Pitaya Programming Examples

A comprehensive collection of programming examples for Red Pitaya boards, demonstrating remote control and on-board programming capabilities across multiple programming languages.

---

## Overview

This repository contains practical examples for programming and controlling Red Pitaya STEMlab boards. The examples cover various functionalities including signal acquisition, generation, digital I/O, communication protocols, and advanced features like deep memory acquisition and logic analysis.

**Programming Options:**
- **Remote Control**: Program Red Pitaya from a remote computer (PC, laptop, etc.)
- **On-Board Execution**: Run programs directly on the Red Pitaya board

**Supported Languages:**
- Python (primary reference with comprehensive examples)
- C
- MATLAB
- LabVIEW (via SCPI/API)

---

## Repository Structure

### `python-api/` (Primary Reference)
Comprehensive Python API examples organized by functionality:

- **Acquisition/** - Data acquisition and sampling examples
- **Acq_Gen/** - Combined acquisition and generation examples
- **Analog/** - Analog input/output operations
- **Digital/** - Digital GPIO and PWM examples
- **Digital_com/** - Digital communication protocols (UART, I2C, SPI, CAN)
- **DMM/** - Direct Memory Mode (DMA/DMG) for high-speed operations
- **Generation/** - Waveform generation examples
- **Hardware/** - Hardware-specific features and configurations
- **LCR/** - LCR meter functionality
- **Logic_analyzer/** - Protocol decoding (UART, SPI, I2C, CAN)
- **Multiboard/** - Multi-board synchronization examples
- **Other/** - Utility scripts and special features
- **Streaming/** - Data streaming examples

All Python examples feature:
- ✅ Comprehensive documentation headers
- ✅ Structured code sections with clear comments
- ✅ Configuration parameters with explanations
- ✅ Error handling and status messages
- ✅ Usage instructions and hardware requirements

### `python/` (Legacy - Being Updated)
Older Python examples that will be restructured to match the `python-api/` organization.

### `C/` (Being Updated)
C programming examples for Red Pitaya. Will be updated to match the structure and documentation standards of `python-api/`.

### `Matlab/` (Being Updated)
MATLAB examples for Red Pitaya control. Will be updated to match the structure and documentation standards of `python-api/`.

### Other Directories
- **Communication/** - Various communication protocol examples
- **Tests/** - Test scripts and validation examples
- **E3_module_code/** - Examples specific to E3 expansion module
- **gpio_sysfs/** - Low-level GPIO access examples
- **uart-arduino/** - UART communication with Arduino
- **web-tutorial/** - Web-based tutorials and examples
- **xadc/** - XADC (analog-to-digital converter) examples

---

## Getting Started

### Prerequisites

**For Remote Programming:**
- Red Pitaya board with network connection
- Compatible software development environment (Python, MATLAB, or C compiler)
- Red Pitaya API libraries installed

**For On-Board Execution:**
- SSH access to Red Pitaya
- Red Pitaya API libraries (pre-installed on official OS)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/RedPitaya/RedPitaya-Examples.git
   cd RedPitaya-Examples
   ```

2. **Python API Setup (Recommended):**
   ```bash
   # Install Red Pitaya Python API (if programming remotely)
   pip install redpitaya-api
   
   # Or use on-board via SSH
   ssh root@rp-xxxxxx.local
   cd /opt/redpitaya/examples/python-api
   ```

3. **Choose your programming language and navigate to the examples:**
   ```bash
   cd python-api/     # For Python examples
   cd C/              # For C examples
   cd Matlab/         # For MATLAB examples
   ```

### Running Examples

**Python Example:**
```bash
python python-api/Acquisition/acq_1.py
```

**On Red Pitaya Board:**
```bash
ssh root@rp-xxxxxx.local
cd /opt/redpitaya/examples/python-api
python Digital/dig_1_led_blink.py
```

---

## Features Covered

The examples in this repository demonstrate:

### Signal Processing
- ⚡ High-speed data acquisition (up to 125 MS/s)
- 🌊 Arbitrary waveform generation
- 📊 Dual-channel synchronized acquisition and generation
- 🎯 Trigger-based capture (edge, level, external)
- 💾 Deep memory mode (DMA) for large data sets

### Digital I/O
- 🔌 GPIO pin control (digital input/output)
- 💡 LED control and status indicators
- ⏱️ PWM (Pulse Width Modulation) generation
- 🔘 Button/switch input handling

### Communication Protocols
- 📡 UART (serial communication)
- 🔗 I2C (Inter-Integrated Circuit)
- 🔄 SPI (Serial Peripheral Interface)
- 🚗 CAN (Controller Area Network)

### Advanced Features
- 🔍 Logic Analyzer with protocol decoding
- 📏 LCR meter functionality
- 🔗 Multiboard synchronization (daisy chain)
- 🌊 Streaming data acquisition
- 🎛️ Hardware configuration and calibration

### Measurement & Analysis
- 📈 Spectrum analysis
- 🎚️ Analog measurements
- 🌡️ Temperature monitoring
- ⚙️ PLL (Phase-Locked Loop) control

---

## Documentation

For detailed API documentation, command references, and programming guides, visit the **Red Pitaya Documentation**:

**Main Documentation:** [Red Pitaya Documentation Website]

Key Documentation Sections:
- **API & Remote Control**: Programming interfaces and remote control capabilities
- **Command Reference**: Complete list of SCPI and API commands
- **Hardware Specifications**: Board specifications and pin configurations
- **Getting Started Guides**: Setup and first steps
- **Application Notes**: Advanced use cases and tutorials

---

## Project Information

### Related Repositories

- **Main RedPitaya Repository**: https://github.com/RedPitaya/RedPitaya
  - Contains the Red Pitaya ecosystem, FPGA designs, and system software

### API Support

- **Python API**: Fully supported with comprehensive examples (recommended)
- **C API**: Supported, examples being updated
- **MATLAB API**: Supported, examples being updated
- **LabVIEW**: Available via SCPI protocol

### Version Compatibility

These examples are compatible with:
- Red Pitaya OS 2.00 and later
- STEMlab 125-14 (and compatible models)
- STEMlab 125-10

---

## Contributing

Contributions are welcome! If you have examples, improvements, or bug fixes:

1. Fork the repository
2. Create a feature branch
3. Make your changes with clear documentation
4. Submit a pull request

Please follow the documentation and code style used in the `python-api/` examples.

---

## Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Forum**: [Red Pitaya Forum](https://forum.redpitaya.com)
- **Documentation**: Red Pitaya official documentation website
- **Email**: support@redpitaya.com

---

## License

Examples repository is released under the GNU GENERAL PUBLIC LICENSE.

---

## Notes

- **SCPI Examples**: The SCPI folder is being phased out and will be moved to legacy/archive. New users should use the language-specific API examples instead.
- **Work in Progress**: Python, C, and MATLAB examples are actively being updated to provide consistent structure and comprehensive documentation.
- **Example Quality**: The `python-api/` folder represents the current standard for example documentation and organization.

---

**Red Pitaya** - Open Source FPGA development board for Test & Measurement
*Built for industry. Engineered for innovation.*
