# Red Pitaya Programming Examples

A curated collection of programming examples for Red Pitaya boards, organized to make it easier to find the right language, interface, or hardware-specific example.

⚠️ **Note:** The repository is undergoing an update to improve organization and documentation. Some examples may be moved or renamed. Please check the individual example documentation for compatibility and requirements.

---

## Overview

This repository contains practical examples for programming and controlling Red Pitaya boards. The examples cover signal acquisition, generation, digital I/O, communication protocols, streaming, logic analysis, and board-specific utilities.

**Programming options:**

- Remote control from a PC or laptop (SCPI commands)
- On-board execution directly on the Red Pitaya board (API commands)

**Supported example sets:**

- API examples:
  - Python
  - C++
- SCPI examples:
  - Python
  - MATLAB
  - LabVIEW
- Legacy SCPI commands (pre 1.04 OS)

**Other resources:**

- Web application tutorials
- E3 module source code
- Arduino examples

⚠️ **Note:** Some examples may require additional hardware or specific Red Pitaya board models. Please check the individual example documentation for compatibility and requirements.

---

## Repository Structure

Examples are organized by feature area. SCPI and API examples share the same directory structure for consistency.

- `Acquisition/` - Data acquisition and sampling
- `Acq_Gen/` - Combined acquisition and generation
- `Analog/` - Analog input/output operations
- `Digital/` - Digital GPIO and PWM examples
- `Digital_com/` - UART, I2C, SPI, and CAN communication
- `DMM/` - Deep Memory Mode for interfacing with RAM containing acquisition and generation examples
- `Generation/` - Signal generation and AWG examples
- `Hardware/` - Hardware-specific features and configuration
- `LCR/` - LCR meter functionality
- `Logic_analyzer/` - Protocol decoding and analysis
- `Multiboard/` - Multi-board synchronization
- `Other/` - Utility scripts and special-purpose examples
- `Socket_client_server/` - Socket-based client/server example
- `Streaming/` - Data streaming examples

## Other Directories

- `Arduino/` - Examples for Arduino-based integration.
- `E3_source_code/` - Source code for the E3 expansion module.
- `web-tutorial/` - Web application tutorials and supporting examples.
- `old/` - Archived or legacy material kept for reference.

---

## Getting Started

### Prerequisites

- Red Pitaya board on the same local network as computer for remote use
- SSH access for on-board execution
- Compatible development environment for the language you want to use

### Installation

1. **Clone the repository** to your local machine:

   ```bash
   git clone https://github.com/RedPitaya/RedPitaya-Examples.git
   cd RedPitaya-Examples
   ```

2. **SCPI examples**: Turn on SCPI server on the Red Pitaya board. Make sure the redpitaya_scpi.py library is in the same folder as the example your want to run (or correctly referenced in the library path).

   ```bash
   python SCPI_examples/Python_SCPI/acq_1_treshold.py
   ```

3. **API examples**: Copy the example files to the Red Pitaya board and ssh into the board to run them. For example:

    ```bash
    scp -r API_examples root@rp-xxxxxx.local:/root
    ```

### Running Examples

SCPI examples:

```bash
python SCPI_examples/Python_SCPI/acq_1_treshold.py
```

On the Red Pitaya board:

```bash
ssh root@rp-xxxxxx.local
cd /root/API-examples/Python-API
python Digital/dig_1_led_blink.py
```

---

## Documentation

For detailed API documentation, command references, and programming guides, visit the [Red Pitaya documentation site](https://redpitaya.readthedocs.io/en/latest/appsFeatures/remoteControl/remoteAndProg.html#programming-and-remote-control-tools).

Key documentation areas include:

- API and remote control
- Command reference
- Hardware specifications
- Getting started guides
- Application notes and tutorials

---

## Project Information

### Related Repositories

- [Main Red Pitaya repository](https://github.com/RedPitaya/RedPitaya)

### Version Compatibility

These examples are compatible with Red Pitaya OS 2.00 and later on all Red Pitaya boards. Check the individual example documentation for any specific requirements or dependencies.

---

## Contributing

Contributions are welcome. If you have examples, improvements, or bug fixes:

1. Fork the repository
2. Create a feature branch
3. Make your changes with clear documentation
4. Submit a pull request

Please follow the structure and documentation style used in the `API_examples/Python_API/` examples.

---

## Support

- Issues: report bugs or request features via GitHub Issues
- [Forum](https://forum.redpitaya.com)
- [Red Pitaya official documentation website](https://redpitaya.readthedocs.io/en/latest/)
- Email: support@redpitaya.com

---

## License

This examples repository is released under the GNU General Public License.

Red Pitaya teachnical team
