# Compiler flags
CFLAGS  = -Wall -std=c++20 ## -Werror
CFLAGS += -I/opt/redpitaya/include
CFLAGS += -I/opt/redpitaya/include/api250-12
LDFLAGS = -L/opt/redpitaya/lib
LDLIBS  = -static -lrp-hw-can -lrp -lrp-hw-calib -lrp-hw-profiles
LDLIBS += -lrp-gpio -lrp-i2c -lrp-hw -lm -lstdc++ -lpthread -li2c -lsocketcan

# Programs organized by subdirectory
ANALOG_PRGS = Analog/analog_inputs \
              Analog/analog_outputs

DIGITAL_PRGS = Digital/digital_led_bar \
               Digital/digital_led_blink \
               Digital/digital_push_button

DIGITAL_COMM_PRGS = Digital_communication/i2c \
                    Digital_communication/spi \
                    Digital_communication/spi_loopback \
                    Digital_communication/uart \
                    Digital_communication/uart_loopback \
                    Digital_communication/can_pass \
                    Digital_communication/can_loopback \
                    Digital_communication/test_e_module \
                    Digital_communication/i2c_eeprom_read_calib \
                    Digital_communication/i2c_switch_max7311

ACQUISITION_PRGS = Acquisition/acquire_trigger_software \
                   Acquisition/acquire_trigger_posedge \
                   Acquisition/acquire_signal_check \
                   Acquisition/acquire_split_trigger \
                   Acquisition/acquire_4ch_trigger_software

GENERATION_PRGS = Generation/generate_arbitrary_waveform \
                  Generation/generate_burst_trigger_external \
                  Generation/generate_burst_trigger_software \
                  Generation/generate_continuous \
                  Generation/generate_two_burst_trigger_software \
                  Generation/generate_two_trigger_software_sync \
                  Generation/generate_continuous_dma

DMM_PRGS = DMM/axi \
           DMM/axi_4ch \
           DMM/axi_without_copy \
           DMM/generate_dma_burst

HARDWARE_PRGS = Hardware/calibration_api

# All programs
ALL_PRGS = $(ANALOG_PRGS) \
           $(DIGITAL_PRGS) \
           $(DIGITAL_COMM_PRGS) \
           $(ACQUISITION_PRGS) \
           $(GENERATION_PRGS) \
           $(DMM_PRGS) \
           $(HARDWARE_PRGS)

# Default target: build everything
all: $(ALL_PRGS)

# Category targets for building specific groups
.PHONY: analog digital digital_comm acquisition generation dmm hardware
analog: $(ANALOG_PRGS)
digital: $(DIGITAL_PRGS)
digital_comm: $(DIGITAL_COMM_PRGS)
acquisition: $(ACQUISITION_PRGS)
generation: $(GENERATION_PRGS)
dmm: $(DMM_PRGS)
hardware: $(HARDWARE_PRGS)

# Pattern rule: build any executable from its corresponding .cpp file
%: %.cpp
	$(CXX) $< $(CFLAGS) $(LDFLAGS) $(LDLIBS) -o $@

# Clean targets
.PHONY: clean clean_all
clean:
	find . -type f -name '*.o' -delete

clean_all: clean
	$(RM) $(ALL_PRGS)

