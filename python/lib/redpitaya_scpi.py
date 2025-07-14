"""
Provides SCPI access to Red Pitaya from host computer.
"""

import socket
from enum import Enum
from typing import List, Optional, Union
import numpy as np

__author__ = "Luka Golinar, Iztok Jeras, Miha Gjura"
__copyright__ = "Copyright 2025, Red Pitaya"


class Waveform(Enum):
    """Waveform types for signal generator."""
    SINE = "SINE"
    SQUARE = "SQUARE"
    TRIANGLE = "TRIANGLE"
    SAWU = "SAWU"
    SAWD = "SAWD"
    PWM = "PWM"
    ARBITRARY = "ARBITRARY"
    DC = "DC"
    DC_NEG = "DC_NEG"

class TriggerSource(Enum):
    """Trigger sources for signal generator."""
    EXT_PE = "EXT_PE"
    EXT_NE = "EXT_NE"
    INT = "INT"
    GATED = "GATED"

class Load(Enum):
    """Load settings for signal generator."""
    INF = "INF"
    L50 = "L50"

class SweepMode(Enum):
    """Sweep modes for signal generator."""
    LINEAR = "LINEAR"
    LOG = "LOG"

class SweepDirection(Enum):
    """Sweep directions for signal generator."""
    NORMAL = "NORMAL"
    UP_DOWN = "UP_DOWN"
    
class Units(Enum):
    """Acquisition data return type."""
    RAW = "RAW"
    VOLTS = "VOLTS"

class DataFormat(Enum):
    """Acquisition data format."""
    BIN = "BIN"
    ASCII = "ASCII"

class Gain(Enum):
    """Input gain settings for oscilloscope."""
    LV = "LV"
    HV = "HV"

class Coupling(Enum):
    """Input coupling settings for oscilloscope."""
    DC = "DC"
    AC = "AC"

class DataTriggerPosition(Enum):
    """Acquisition data trigger position type."""
    PRE_TRIG = "PRE_TRIG"
    POST_TRIG = "POST_TRIG"
    PRE_POST_TRIG = "PRE_POST_TRIG"

class UartBits(Enum):
    """UART bits settings."""
    CS6 = "CS6"
    CS7 = "CS7"
    CS8 = "CS8"

class UartParity(Enum):
    """UART parity settings."""
    NONE = "NONE"
    EVEN = "EVEN"
    ODD = "ODD"
    MARK = "MARK"
    SPACE = "SPACE"

class SPIMode(Enum):
    """SPI mode settings."""
    LISL = "LISL"
    LIST = "LIST"
    HISL = "HISL"
    HIST = "HIST"
    
class SPICSMode(Enum):
    """SPI chip select mode settings"""
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    
class CANMode(Enum):
    """CAN mode settings."""
    LOOPBACK = "LOOPBACK"
    LISTEN_ONLY = "LISTEN_ONLY"
    SAMPLES = "3_SAMPLES"
    ONE_SHOT = "ONE_SHOT"
    BERR_REPORTING = "BERR_REPORTING"
    
class CANState(Enum):
    """CAN state settings."""
    ERROR_ACTIVE = "ERROR_ACTIVE"
    ERROR_WARNING = "ERROR_WARNING"
    ERROR_PASSIVE = "ERROR_PASSIVE"
    BUS_OFF = "BUS_OFF"
    STOPPED = "STOPPED"
    SLEEPING = "SLEEPING"
    
class LCRMode(Enum):
    """LCR meter mode settings."""
    SERIES = "SERIES"
    PARALLEL = "PARALLEL"
    
class LCRExtMode(Enum):
    """LCR meter extended mode settings."""
    LCR_EXT = "LCR_EXT"
    CUSTOM = "CUSTOM"

class LCRExtShunt(Enum):
    """LCR meter extended shunt settings."""
    S10 = "S10"
    S100 = "S100"
    S1K = "S1k"
    S10K = "S10k"
    S100K = "S100k"
    S1M = "S1M"

class scpi (object):
    """SCPI class used to access Red Pitaya over an IP network."""
    delimiter = '\r\n'


    ####################################################
    ###    Functions for establishing connection     ###
    ####################################################
    #
    #! Functions in this section should not be modified as they take care of the communication between Red Pitaya and the computer
    #

    def __init__(self, host: str, timeout: Optional[float]=None, port: int=5000):
        """Initialize object and open IP connection.
        Host IP should be a string in parentheses, like '192.168.1.100' or 'rp-xxxxxx.local'.
        """
        self.host    = host
        self.port    = port
        self.timeout = timeout

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if timeout is not None:
                self._socket.settimeout(timeout)

            self._socket.connect((host, port))

        except socket.error as e:
            print('SCPI >> connect({!s:s}:{:d}) failed: {!s:s}'.format(host, port, e))

    def __del__(self):
        if self._socket is not None:
            self._socket.close()
        self._socket = None

    def close(self):
        """Close IP connection."""
        self.__del__()

    def rx_txt(self, chunksize: int = 4096):
        """Receive text string and return it after removing the delimiter."""
        msg = ''
        while 1:
            chunk = self._socket.recv(chunksize).decode('utf-8')        # Receive chunk size of 2^n preferably
            msg += chunk
            if (len(msg) >= 2 and msg[-2:] == self.delimiter):
                return msg[:-2]

    def rx_txt_check_error(self, chunksize: int = 4096, stop: bool = True):
        """Receive text string and return it after removing the delimiter.
        Check for error."""
        msg = self.rx_txt(chunksize)
        self.check_error(stop)
        return msg

    def rx_arb(self):
        """ Recieve binary data from scpi server"""
        numOfBytes = 0
        data=b''
        while len(data) != 1:
            data = self._socket.recv(1)
        if data != b'#':
            return False
        data=b''

        while len(data) != 1:
            data = self._socket.recv(1)
        numOfNumBytes = int(data)
        if numOfNumBytes <= 0:
            return False
        data=b''

        while len(data) != numOfNumBytes:
            data += (self._socket.recv(1))
        numOfBytes = int(data)
        data=b''

        while len(data) < numOfBytes:
            r_size = min(numOfBytes - len(data),4096)
            data += (self._socket.recv(r_size))

        self._socket.recv(2)        # recive \r\n

        return data

    def rx_arb_check_error(self, stop: bool = True):
        """ Recieve binary data from scpi server. Check for error."""
        data = self.rx_arb()
        self.check_error(stop)
        return data

    def tx_txt(self, msg: str):
        """Send text string ending and append delimiter."""
        return self._socket.sendall((msg + self.delimiter).encode('utf-8'))     # was send(().encode('utf-8'))

    def tx_txt_check_error(self, msg: str, stop: bool= True):
        """Send text string ending and append delimiter. Check for error."""
        self.tx_txt(msg)
        self.check_error(stop)

    def txrx_txt(self, msg: str):
        """Send/receive text string."""
        self.tx_txt(msg)
        return self.rx_txt()

    def check_error(self, stop = True):
        """Read error from Red Pitaya and print it."""
        res = int(self.stb_q())
        if (res & 0x4):
            while 1:
                err = self.err_n()
                if (err.startswith('0,')):
                    break
                print(err)
                n = err.split(",")
                if (len(n) > 0 and stop and int(n[0]) > 9500):
                    exit(1)


    ###########################################
    ###       SCPI command functions        ###
    ###########################################
    #
    # NOTE: The functions in this section are meant to work with the latest release of the Red Pitaya OS and may not work on older versions
    #       due to the introduction of new commands which the functions use, but might not be available in your current OS version.
    #       Please check the available commands in the ecosystem column here: https://redpitaya.readthedocs.io/en/latest/appsFeatures/remoteControl/command_list.html
    #
    # You are free to modify the functions in this section.
    #

    ### BOARD CONTROL ###

    def board_info(
        self
    ) -> List[str]:
        """
        Returns Red Pitaya board ID and model name.
        """
        settings = []

        settings.append(self.txrx_txt('SYSTem:BRD:ID?'))
        settings.append(self.txrx_txt('SYSTem:BRD:Name?'))
        self.check_error()

        #? Remove prints?
        print(f"Red Pitaya board ID: {settings[0]}")
        print(f"Red Pitaya board Name: {settings[1]}")

        return settings

    def board_set_date_time(
        self,
        date: str,
        time: str,
    ) -> None:
        """
        Sets the Linux OS date and time on the Red Pitaya board.

        Args:
            date (str): Date in format "YYYY-MM-DD".
            time (str): Time in format "hh:mm:ss.s".

        """

        self.tx_txt(f"SYSTem:DATE \"{date}\"")
        self.tx_txt(f"SYSTem:TIME \"{time}\"")
        self.check_error()

    def board_get_date_time(
        self
    ) -> str:
        """
        Returns the Linux OS date and time on the Red Pitaya board.

        Returns:
            str: Date and time in format "YYYY-MM-DD hh:mm:ss" 
        """
        date = self.txrx_txt("SYSTem:DATE?")
        time = self.txrx_txt("SYSTem:TIME?")
        self.check_error()

        return f"{date} {time}"

    def help(
        self
    ) -> None:
        """
        Prints all available SCPI commands for the current Red Pitaya OS.
        """
        available_commands = self.txrx_txt("SYSTem:Help?")
        self.check_error()
        print(f"\nAvailable SCPI commands for the current Red Pitaya OS:\n{available_commands}\n")

    ### LED & GPIO ###
    #TODO add digital_set(), digital_get_settings()

    ### ANALOG IO ###
    def analog_get_data(
        self
    ) -> np.ndarray:
        """
        Return data from all 4 slow analog inputs as a numpy array.
        """
        data = np.array([self.txrx_txt(f"ANALOG:PIN? AIN{i}") for i in range(4)], dtype=float)
        self.check_error()

        return data

    ### DAISY CHAIN ###

    def daisy_set(
        self,
        x_channel: bool = False,
        click_shield: bool = False,
        trig_mode: Optional[str] = None
    ) -> None:
        """
        Configure the settings for the daisy chain for the selected Red Pitaya board configuration.

        Args:
            x_channel (bool, optional): Set to `True` if using X-channel system. Defaults to False.
            click_shield (bool, optional): Set to `True` if using Red Pitaya Click Shields. Defaults to False.
            trig_mode (str, optional): Trigger source to be shared (either "adc" or "dac"). Click Shields only. Defaults to None.
        """
        trig_mode_list = ["ADC", "DAC"]

        # Check for errors
        if trig_mode is not None and trig_mode.upper() not in trig_mode_list:
            raise ValueError(f"{trig_mode.upper()} is not a defined trigger source")
    
        if x_channel:
            # Set up X-channel daisy chain
            self.tx_txt("DAISY:SYNC:CLK ON")
            self.tx_txt("DAISY:SYNC:TRIG ON")

        elif click_shield:
            # Set up Click Shield daisy chain
            self.tx_txt("DAISY:TRig:Out:ENable ON")
            if trig_mode is not None:
                self.tx_txt(f"DAISY:TRig:Out:SOUR {trig_mode.upper()}")
        self.check_error()

    def daisy_get_settings(
        self
    ) -> List[str | None]:
        """
        Returns the current Daisy chain settings
        [clk_sync, trig_sync, trig_out_en, trig_out_sour]

        Returns:
            str: Daisy chain settings.
        """
        settings = [
            self.txrx_txt("DAISY:SYNC:CLK?"),
            self.txrx_txt("DAISY:SYNC:TRIG?"),
            self.txrx_txt("DAISY:TRig:Out:ENable?"),
            self.txrx_txt("DAISY:TRig:Out:SOUR?")
        ]
        self.check_error()

        #? Remove prints?
        print(f"SATA clock sync: {settings[0]}")
        print(f"SATA trigger sync: {settings[1]}")
        print(f"DIO0_N trigger output enable: {settings[2]}")
        print(f"Trigger output source: {settings[3]}")

        return settings


    ### PLL ###

    def pll_enable(
        self,
        siglab: bool = False
    ) -> None:
        """
        Enables Phase Locked Loop control on SIGNALlab 250-12. This syncs the SIGNALlab 250-12 with the 10 MHz
        reference clock supplyied through the SMA connector on the back of the unit.

        Args:
            siglab (bool, optional): Set to true if using SIGNALlab 250-12. Defaults to `False`.
        """
        if siglab:
            self.tx_txt("RP:PLL:ENable ON")
            self.check_error()
        else:
            print("PLL is only available on SIGNALlab 250-12")

    def pll_disable(
        self,
        siglab: bool = False
    ) -> None:
        """
        Disables Phase Locked Loop control on SIGNALlab 250-12. This syncs the SIGNALlab 250-12 with the 10 MHz
        reference clock supplyied through the SMA connector on the back of the unit.

        Args:
            siglab (bool, optional): Set to true if using SIGNALlab 250-12. Defaults to `False`.
        """

        if siglab:
            self.tx_txt("RP:PLL:ENable OFF")
            self.check_error()
        else:
            print("PLL is only available on SIGNALlab 250-12")

    def pll_get_state(
        self,
        siglab: bool = False
    ) -> List[str | None]:
        """
        Returns whether PLL control is enables and the status of the PLL lock to the 10 MHz reference clock
        supplyied through the SMA connector on the back of the unit.
        Only available on SIGNALlab 250-12.

        Args:
            siglab (bool, optional): Set to true if using SIGNALlab 250-12. Defaults to `False`.
        """

        settings = []

        if siglab:
            pll_enable = self.txrx_txt("RP:PLL:ENable?")
            pll_state = self.txrx_txt("RP:PLL:STATE?")
            self.check_error()
            settings = [pll_enable, pll_state]

        #? Remove prints?
            print(f"PLL Enable: {settings[0]}")
            print(f"PLL synchronisation status: {settings[1]}")
        else:
            print("PLL is only available on SIGNALlab 250-12")

        return settings


    ### GENERATOR ###
    #TODO check SCPI commands

    # Continuous
    def gen_set(
        self,
        chan: int,
        func: Waveform = Waveform.SINE,
        volt: float = 1,
        freq: float = 1000,
        offset: Optional[float] = None,
        phase: Optional[float] = None,
        dcyc: Optional[float] = None,
        data: Optional[np.ndarray] = None,
        trig_sour: Optional[TriggerSource] = None,
        ext_trig_deb_us: Optional[int] = None,
        ext_trig_lev: Optional[float] = None,
        load: Optional[Load] = None,
        sdrlab: bool = False,
        siglab: bool = False
    ) -> None:

        """
        Set the parameters for signal generator on one channel.

        Args:
            chan (int) :
                Output channel (either 1 or 2).
            func (str, optional) :
                Waveform of the signal (SINE, SQUARE, TRIANGLE, SAWU,
                SAWD, PWM, ARBITRARY, DC, DC_NEG).
                Defaults to `sine`.
            volt (int, optional) :
                Amplitude of signal {-1, 1} Volts. {-5, 5} for SIGNALlab 250-12.
                Defaults to 1.
            freq (int, optional) :
                Frequency of signal. Not relevant if 'func' is "DC" or "DC_NEG".
                Defaults to 1000.
            offset (int, optional) :
                Signal offset {-1, 1} Volts. {-5, 5} for SIGNALlab 250-12.
                Defaults to 0 (None).
            phase (int, optional) :
                Phase of signal {-360, 360} degrees.
                Defaults to 0 (None).
            dcyc (float, optional) :
                Duty cycle, where 1 corresponds to 100%.
                Defaults to 0.5 (None).
            data (ndarray, optional) :
                Numpy ``ndarray`` of max 16384 values, floats in range {-1,1}
                (or {-5,5} for SIGNALlab).
                Define the custom waveform if "func" is "ARBITRARY".
                Defaults to `None`.
            trig_sour (str, optional):
                Trigger source (EXT_PE, EXT_NE, INT, GATED).
                Defaults to `int` (internal).
            ext_trig_deb_us (int, optional):
                External trigger debounce filter length in microseconds. Pulses shorter
                than the setting will not count as a triggering moment.
                Defaults to 500 (None).
            ext_trig_lev (float, optional):
                External trigger level in Volts.
                Defaults to 1 (None).
                (SIGNALlab 250-12 only).
            load (str, optional):
                Expected generator load (INF or L50).
                Defaults to `INF`.
                (SIGNALlab 250-12 only).
            sdrlab (bool, optional):
                `True` if operating with SDRlab 122-16.
                Defaults to `False`.
            siglab (bool, optional):
                `True` if operating with SIGNALlab 250-12.
                Defaults to `False`.

        The settings will work on any Red Pitaya board. If operating on a board
        other than STEMlab 125-14, change the bool value of the appropriate
        parameter to true (sdrlab, siglab)
        """
        self._validate_gen_set_params(chan, func, volt, freq, offset, phase, dcyc, data, trig_sour, ext_trig_deb_us, ext_trig_lev, load, sdrlab, siglab)

        # Load needs to be set before the amplitude
        if siglab:
            if ext_trig_lev is not None:
                self.tx_txt(f"TRig:EXT:LEV {ext_trig_lev}")
            if load is not None:
                self.tx_txt(f"SOUR{chan}:LOAD {load.value}")

        self.tx_txt(f"SOUR{chan}:FUNC {func.value}")
        self.tx_txt(f"SOUR{chan}:VOLT {volt}")

        if func not in {Waveform.DC, Waveform.DC_NEG}:
            self.tx_txt(f"SOUR{chan}:FREQ:FIX {freq}")

        if offset is not None:
            self.tx_txt(f"SOUR{chan}:VOLT:OFFS {offset}")
        if phase is not None:
            self.tx_txt(f"SOUR{chan}:PHAS {phase}")
        if func == Waveform.PWM and dcyc is not None:
            self.tx_txt(f"SOUR{chan}:DCYC {dcyc}")
        if data is not None and func == Waveform.ARBITRARY:
            cust_wf = ",".join(map(str, data))
            self.tx_txt(f"SOUR{chan}:TRAC:DATA:DATA {cust_wf}")
        if trig_sour is not None:
            self.tx_txt(f"SOUR{chan}:TRig:SOUR {trig_sour.value}")
        if ext_trig_deb_us is not None:
            self.tx_txt(f"SOUR:TRig:EXT:DEBouncer:US {ext_trig_deb_us}")

        self.check_error()

    def gen_get_settings(self, chan: int, siglab: bool = False) -> List[str | None]:
        """
        Retrieves generator settings of one channel from Red Pitaya, prints them in the console and return
        an array with the following sequence:
        [func, volt, freq, offs, phas, dcyc, trig_sour, ext_trig_deb_us, ext_trig_lev, load]

            Func            - Signal waveform (sine, triangle, square, ...)
            Voltage         - One-way amplitude
            Freq            - Signal frequency
            Offs            - Offset from zero
            Phas            - Phase delay
            Dcyc            - Duty Cycle
            Trig_sour       - Trigger source
            Ext_trig_deb_us - External trigger debounce filter value in microseconds. Common for both channels.
            Ext_trig_lev    - External trigger level (SIGNALlab only). Common for both channels.
            Load            - Generator load setting (SIGNALlab only)

        Checks and displays SCPI command errors.

        Args:
            chan (int):
                Output channel (either 1 or 2).
            siglab (bool, optional):
                Set to `True` if using SIGNALlab 250-12, otherwise leave blank.

        Returns:
            str: Generator settings for the specified channel.
        """

        settings = [
            self.txrx_txt(f"SOUR{chan}:FUNC?"),
            self.txrx_txt(f"SOUR{chan}:VOLT?"),
            self.txrx_txt(f"SOUR{chan}:FREQ:FIX?"),
            self.txrx_txt(f"SOUR{chan}:VOLT:OFFS?"),
            self.txrx_txt(f"SOUR{chan}:PHAS?"),
            self.txrx_txt(f"SOUR{chan}:DCYC?"),
            self.txrx_txt(f"SOUR{chan}:TRig:SOUR?"),
            self.txrx_txt("SOUR:TRig:EXT:DEBouncer:US?")
        ]

        if siglab:
            settings.append(self.txrx_txt("TRig:EXT:LEV?"))
            settings.append(self.txrx_txt(f"SOUR{chan}:LOAD?"))

        self.check_error()

        #? Remove prints? Repace with logging?
        print(f"Generator channel {chan} settings:")
        print(f"Waveform/function: {settings[0]}")
        print(f"Amplitude: {settings[1]} V")    
        print(f"Frequency: {settings[2]} Hz")
        print(f"Offset: {settings[3]} V")
        print(f"Phase: {settings[4]} deg")
        print(f"Duty Cycle: {settings[5]}")
        print(f"Trigger source: {settings[6]}")
        print(f"External trigger debouncer filter: {settings[7]} us")

        if siglab:
            print(f"External trigger level: {settings[8]} V")
            print(f"Load: {settings[9]}")

        return settings

    # Burst
    def gen_burst_enable(self, chan: int) -> None:
        """
        Enables burst mode for the specified channel.
        """

        self._validate_channel(chan)
        self.tx_txt(f"SOUR{chan}:BURS:STAT BURST")
        self.check_error()

    def gen_burst_disable(self, chan: int) -> None:
        """
        Disables burst mode for the specified channel.
        """
        self._validate_channel(chan)
        self.tx_txt(f"SOUR{chan}:BURS:STAT CONTINUOUS")
        self.check_error()

    def gen_burst_set(
        self,
        chan: int,
        ncyc: int = 1,
        nor: int = 1,
        period: Optional[int] = None,
        init_val: float = 0,
        last_val: float = 0,
        siglab: bool = False
    ) -> None:
        """
        Set the parameters for burst mode on one channel. Generate "nor" number of "ncyc" periods with total time "period". 
        Waveform shape, amplitude, offset, phase, and duty cycle are inherited from ``gen_set()`` function.
        Automatically turns on Burst mode.

        Args:
            chan (int) :
                Output channel (either 1 or 2).
            ncyc (int, optional) : 
                Number of signal periods in one burst (Number of cycles).
                Defaults to 1.
            nor (int, optional) : 
                Number of repeated bursts.
                Defaults to 1.
            period (int, optional) :
                Total time of one burst in µs {1, 5e8}. Includes the signal and delay.
                Defaults to `None`.
            init_val (float, optional):
                Start value of the burst signal in Volts. The voltage that is on the
                line before the first burst pulse is generated.
                Defaults to 0.
            last_val (float, optional):
                End value of the burst signal in Volts. The line will stay on this
                voltage until a new burst is generated.
                Defaults to 0.
            siglab (bool, optional): 
                Set to `True` if using SIGNALlab 250-12, otherwise leave blank.
                Defaults to `False`.

            The settings will work on any Red Pitaya board.
        """
        self._validate_burst_params(chan, ncyc, nor, period, init_val, last_val, siglab)

        self.tx_txt(f"SOUR{chan}:BURS:STAT BURST")
        self.tx_txt(f"SOUR{chan}:BURS:NCYC {ncyc}")
        self.tx_txt(f"SOUR{chan}:BURS:NOR {nor}")

        if period is not None:
            self.tx_txt(f"SOUR{chan}:BURS:INT:PER {period}")

        self.tx_txt(f"SOUR{chan}:BURS:LASTValue {last_val}")
        self.tx_txt(f"SOUR{chan}:INITValue {init_val}")

        self.check_error()

    def gen_get_burst_settings(self, chan: int) -> List[str | None]:
        """
        Retrieves burst generator settings of one channel from Red Pitaya, prints them in the console and returns
        an array with the following sequence:
        [mode, ncyc, nor, period, init_val, last_val]

            Mode        - Generator mode (burst/continuous)
            Ncyc        - Number of signal periods in one burst (number of cycles)
            Nor         - Number of repeated bursts (number of repetitions)
            Period      - Total time of one burst in µs. Includes the signl and delay between two consecutive bursts.
            Init_val    - Starting value of the burst signal in Volts.
            Last_val    - End value of the burst signal in Volts.

        Args:
            chan (int): Output channel (either 1 or 2).

        Returns:
            str: Burst generator settings for the specified channel.
        """

        settings = [
            self.txrx_txt(f"SOUR{chan}:BURS:STAT?"),
            self.txrx_txt(f"SOUR{chan}:BURS:NCYC?"),
            self.txrx_txt(f"SOUR{chan}:BURS:NOR?"),
            self.txrx_txt(f"SOUR{chan}:BURS:INT:PER?"),
            self.txrx_txt(f"SOUR{chan}:BURS:INITValue?"),
            self.txrx_txt(f"SOUR{chan}:LASTValue?")
        ]

        self.check_error()

        #? Remove prints? Repace with logging?
        print(f"Generator channel {chan} burst settings:")
        print(f"Burst mode: {settings[0]}")
        print(f"NCYC: {settings[1]}")
        print(f"NOR: {settings[2]}")
        print(f"Period: {settings[3]} us")
        print(f"Init value: {settings[4]} V")
        print(f"Last value: {settings[5]} V")

        return settings

    # Sweeep
    def gen_sweep_set(
        self,
        chan: int,
        start_freq: int = 1000,
        stop_freq: int = 10000,
        time_us: int = 1,
        mode: SweepMode = SweepMode.LINEAR,
        direction: SweepDirection = SweepDirection.NORMAL,
        sdrlab: bool = False
    ) -> None:
        """
        Set the parameters for sweep mode on one channel.
        Waveform shape, amplitude, offset, phase, and duty cycle are inherited from ``gen_set()`` function.
        Automatically turns on Sweep mode.

        Args:
            chan (int):
                Output channel (either 1 or 2).
            start_freq (int, optional):
                Start frequency of sweep signal. Defaults to 1000.
            stop_freq (int, optional):
                Stop/End frequency of sweep signal. Defaults to 10000.
            time_us (int, optional):
                Sweep mode transition time in microseconds. How long the generator takes to generate
                the full sweep from ``start_freq`` to ``stop_freq``. When a direction different than
                "NORMAL", it indicates the sweep time in one direction.
                Defaults to 1.
            mode (str, optional):
                Either linear ("LINEAR") or logarithmic("LOG"). Defaults to "LINEAR".
            dir (str, optional):
                Sweep direction ("NORMAL" or "UP_DOWN"). Defaults to "NORMAL".
            sdrlab (bool, optional):
                `True` if operating with SDRlab 122-16. Defaults to `False`.
        
        The settings will work on any Red Pitaya board.
        """

        self._validate_sweep_params(chan, start_freq, stop_freq, time_us, mode, direction, sdrlab)

        self.tx_txt(f"SOUR{chan}:SWeep:STATE ON")
        self.tx_txt(f"SOUR{chan}:SWeep:FREQ:START {start_freq}")
        self.tx_txt(f"SOUR{chan}:SWeep:FREQ:STOP {stop_freq}")
        self.tx_txt(f"SOUR{chan}:SWeep:TIME {time_us}")
        self.tx_txt(f"SOUR{chan}:SWeep:MODE {mode.value}")
        self.tx_txt(f"SOUR{chan}:SWeep:DIR {direction.value}")

        self.check_error()

    def gen_get_sweep_settings(self, chan: int) -> List[str | None]:
        """
        Retrieves sweep mode settings of one channel from Red Pitaya, prints them in the console and returns
        an array with the following sequence:
        [state, start_freq, stop_freq, time_us, mode, dir]

            State       - State of sweep mode generator (ON/OFF)
            Start_freq  - Sweep start frequency 
            Stop_freq   - Sweep stop frequency
            Time_us     - Sweep time in us
            Mode        - Sweep mode
            Dir         - Sweep direction

        Parameters
        ----------
            channel (int): Output channel (either 1 or 2).

        """

        settings = [
            self.txrx_txt(f"SOUR{chan}:SWeep:STATE?"),
            self.txrx_txt(f"SOUR{chan}:SWeep:FREQ:START?"),
            self.txrx_txt(f"SOUR{chan}:SWeep:FREQ:STOP?"),
            self.txrx_txt(f"SOUR{chan}:SWeep:TIME?"),
            self.txrx_txt(f"SOUR{chan}:SWeep:MODE?"),
            self.txrx_txt(f"SOUR{chan}:SWeep:DIR?")
        ]

        self.check_error()

        #? Remove prints? Repace with logging?
        print(f"Sweep mode state: {settings[0]}")
        print(f"Sweep start frequency: {settings[1]}")
        print(f"Sweep stop frequency: {settings[2]}")
        print(f"Sweep time: {settings[3]}")
        print(f"Sweep mode: {settings[4]}")
        print(f"Sweep direction: {settings[5]}")

        return settings

    def gen_sweep_enable(self, chan: int) -> None:
        """
        Enables sweep mode for the specified channel.
        """
        self._validate_channel(chan)
        self.tx_txt(f"SOUR{chan}:SWeep:STATE ON")
        self.check_error()

    def gen_sweep_disable(self, chan: int) -> None:
        """
        Disables sweep mode for the specified channel.
        """
        self._validate_channel(chan)
        self.tx_txt(f"SOUR{chan}:SWeep:STATE OFF")
        self.check_error()

    def gen_sweep_pause(self, chan: int) -> None:
        """
        Pauses the sweep mode for the specified channel.
        """
        self._validate_channel(chan)
        self.tx_txt(f"SOUR{chan}:SWeep:PAUSE ON")
        self.check_error()

    def gen_sweep_resume(self, chan: int) -> None:
        """
        Resumes the sweep mode for the specified channel.
        """
        self._validate_channel(chan)
        self.tx_txt(f"SOUR{chan}:SWeep:PAUSE OFF")
        self.check_error()


    # Validations
    def _validate_gen_set_params(
        self,
        chan: int,
        func: Waveform,
        volt: float,
        freq: float,
        offset: Optional[float],
        phase: Optional[float],
        dcyc: Optional[float],
        data: Optional[np.ndarray],
        trig_sour: Optional[TriggerSource],
        ext_trig_deb_us: Optional[int],
        ext_trig_lev: Optional[float],
        load: Optional[Load],
        sdrlab: bool,
        siglab: bool
    ) -> None:
        """
        Validate parameters for gen_set function.
        """
        waveform_list = [e.value for e in Waveform]
        trigger_list = [e.value for e in TriggerSource]
        load_list = [e.value for e in Load]
        buff_size = 16384

        volt_lim = 5 if siglab else 1
        offs_lim = 5 if siglab else 1
        phase_lim = 360
        freq_up_lim = 60e6 if sdrlab else 50e6
        freq_down_lim = 300e3 if sdrlab else 0

        assert chan in (1, 2), "Channel needs to be either 1 or 2"
        assert func.value in waveform_list, f"{func.value} is not a defined waveform"
        assert freq_down_lim <= freq <= freq_up_lim, f"Frequency is out of range {freq_down_lim, freq_up_lim} Hz"
        assert abs(volt) <= volt_lim, f"Amplitude is out of range {-volt_lim, volt_lim} V"
        if offset is not None:
            assert abs(offset) <= offs_lim, f"Offset is out of range {-offs_lim, offs_lim} V"
        if dcyc is not None:
            assert 0 <= dcyc <= 1, "Duty Cycle is out of range {0, 1}"
        if phase is not None:
            assert abs(phase) <= phase_lim, f"Phase is out of range {-phase_lim, phase_lim} deg"
        if data is not None:
            assert data.shape[0] <= buff_size, f"Data array is too long. Max length is {buff_size}"
        if trig_sour is not None:
            assert trig_sour.value in trigger_list, f"{trig_sour.value} is not a defined trigger source"
        if ext_trig_deb_us is not None:
            assert ext_trig_deb_us >= 1, f"External trigger debounce filter value {ext_trig_deb_us} is out of range. The minimal value is 1 microsecond"
        if ext_trig_lev is not None:
            assert abs(ext_trig_lev) <= volt_lim, f"External trigger level is out of range {-volt_lim, volt_lim} V"
        if load is not None:
            assert load.value in load_list, f"{load.value} is not a defined load for SIGNALlab 250-12"
        assert not (siglab and sdrlab), "Please select only one board option. 'siglab' and 'sdrlab' cannot be true at the same time."

    def _validate_burst_params(
        self,
        chan: int,
        ncyc: int,
        nor: int,
        period: Optional[int],
        init_val: float,
        last_val: float,
        siglab: bool
    ) -> None:
        """
        Validate parameters for gen_burst_set function.
        """
        volt_lim = 5.0 if siglab else 1.0

        self._validate_channel(chan)
        assert ncyc >= 1, "NCYC minimum is 1"
        assert nor >= 1, "NOR minimum is 1"
        if period is not None:
            assert period >= 1, "Minimal burst period 1 µs"
        assert abs(last_val) <= volt_lim, f"Last value is out of range {-volt_lim, volt_lim} V"
        assert abs(init_val) <= volt_lim, f"Init value is out of range {-volt_lim, volt_lim} V"

    def _validate_sweep_params(
        self,
        chan: int,
        start_freq: int,
        stop_freq: int,
        time_us: int,
        mode: SweepMode,
        direction: SweepDirection,
        sdrlab: bool
    ) -> None:
        """
        Validate parameters for gen_sweep_set function.
        """
        freq_up_lim = 60e6 if sdrlab else 50e6
        freq_down_lim = 300e3 if sdrlab else 0

        self._validate_channel(chan)
        assert freq_down_lim < start_freq <= freq_up_lim, f"Start frequency is out of range {freq_down_lim, freq_up_lim} Hz"
        assert freq_down_lim < stop_freq <= freq_up_lim, f"Stop frequency is out of range {freq_down_lim, freq_up_lim} Hz"
        assert start_freq < stop_freq, "Start frequency must be lower than Stop frequency"
        assert time_us >= 1, "Minimal sweep period 1 µs"
        assert mode in SweepMode, f"{mode.value} is not a defined sweep mode"
        assert direction in SweepDirection, f"{direction.value} is not a defined sweep direction"

    def _validate_channel(self, chan: int) -> None:
        """
        Validate the channel number.
        """
        assert chan in (1, 2), "Channel needs to be either 1 or 2"

    ### ACQUISITION ###

    def acq_set(
        self,
        dec: int = 1,
        units: Optional[Units] = None,
        data_format: Optional[DataFormat] = None,
        averaging: bool = True,
        gain: Optional[List[Gain]] = None,
        coupling: Optional[List[Coupling]] = None,
        siglab: bool = False,
        input4: bool = False
    ) -> None:

        """
        Set the parameters for the standard signal acquisition.

        Parameters
        -----------

            dec (int, optional) : 
                Decimation (1, 2, 4, 8, 16, 17, 18, ..., 65535, 65536)
                Defaults to 1.
            units (str, optional) :
                The units in which the acquired data will be returned.
                Defaults to "VOLTS".
            data_format (str, optional) :
                The format in which the acquired data will be returned.
                Defaults to "ASCII".
            averaging (bool, optional) :
                Enable/disable averaging. When True, if decimation is higher than 1,
                each returned sample is the average of the taken samples. For example,
                if dec = 4, the returned sample will be the average of the 4 decimated
                samples.
                Defaults to True.
            gain (list(str), optional) :
                HV / LV - (High (1:20) or Low (1:1 attenuation)) 
                The first element in list applies to the SOUR1 and the second to SOUR2.
                Refers to jumper settings on Red Pitaya fast analog inputs.
                (1:20 and 1:1 attenuator for SIGNALlab 250-12)
                Defaults to "None".
            coupling (list(str), optional) :
                AC / DC - coupling mode for fast analog inputs.
                The first element in list applies to the SOUR1 and the second to SOUR2.
                (Only SIGNALlab 250-12)
                Defaults to "None".
            siglab (bool, optional) :
                Set to True if operating with SIGNALlab 250-12.
                Defaults to False.
            input4 (bool, optional) :
                Set to True if operating with STEMlab 125-14 4-Input.
                Defaults to False.

        The settings will work on any Red Pitaya board. If operating on SIGNALlab 250-12
        or STEMlab 125-14 4-Input change the bool value of the appropriate parameter to
        true (siglab, input4). This will change the available range of input parameters.
        """
        self._validate_acq_set_params(dec, units, data_format, gain, coupling, siglab, input4)

        #!!!!! n = 4 if input4 else 2

        self.tx_txt(f"ACQ:DEC:Factor {dec}")
        self.tx_txt(f"ACQ:AVG {'ON' if averaging else 'OFF'}")
        if units is not None:
            self.tx_txt(f"ACQ:DATA:Units {units.value}")
        if data_format is not None:
            self.tx_txt(f"ACQ:DATA:FORMAT {data_format.value}")

        if gain is not None:
            for i, g in enumerate(gain, start=1):
                self.tx_txt(f"ACQ:SOUR{i}:GAIN {g.value}")
        if coupling is not None and siglab:
            for i, c in enumerate(coupling, start=1):
                self.tx_txt(f"ACQ:SOUR{i}:COUP {c.value}")

        self.check_error()

    def acq_get_settings(self, siglab: bool = False, input4: bool = False) -> List[str | None]:
        """
        Retrieves the standard acquisition settings from Red Pitaya, prints them in console and returns
        them as an array with the following sequence:
        [dec_factor, avearge, units, data_format, buf_size, gain_ch1, gain_ch2, coup_ch1, coup_ch2]
                                                                              , gain_ch3, gain_ch4
            Dec_factor      - Current decimation factor
            Average         - Current averaging status (ON/OFF)
            Units           - Acquisition units (V, RAW)
            Data_format     - Acquisition data format (ASCII, BIN)
            Buf_size        - Buffer size
            Gain_ch1-4      - Current gain on channels (CH3 and CH4 STEMlab 125-14 4-Input only)
            Coup_ch1/2      - Current coupling mode for both channels (AC/DC) (SIGNALlab only)

        Note:   The last two array elements won't exist if siglab = False
                Gain of channels 3 and 4 only if input4 = True

        Parameters
        ----------
            siglab (bool, optional):
                Set to True if operating with SIGNALlab 250-12.
                Defaults to False.
            input4 (bool, optional):
                Set to True if operating with STEMlab 125-14 4-Input.
                Defaults to False.

        """
        self._validate_board(siglab, input4)

        n = 4 if input4 else 2

        settings = [
            self.txrx_txt("ACQ:DEC:Factor?"),
            self.txrx_txt("ACQ:AVG?"),
            self.txrx_txt("ACQ:DATA:Units?"),
            self.txrx_txt("ACQ:DATA:FORMAT?"),
            self.txrx_txt("ACQ:BUF:SIZE?")
        ]

        for i in range(n):
            settings.append(self.txrx_txt(f"ACQ:SOUR{i+1}:GAIN?"))

        if siglab:
            for i in range(2):
                settings.append(self.txrx_txt(f"ACQ:SOUR{i+1}:COUP?"))
        self.check_error()

        #? Remove prints? Repace with logging?
        print(f"Decimation Factor: {settings[0]}")
        print(f"Averaging: {settings[1]}")
        print(f"Units: {settings[2]}")
        print(f"Data format: {settings[3]}")
        print(f"Buffer size: {settings[4]}")

        if input4:
            print(f"Gain CH1/CH2/CH3/CH4: {settings[5]}, {settings[6]}, {settings[7]}, {settings[8]}")
        else:
            print(f"Gain CH1/CH2: {settings[5]}, {settings[6]}")

        if siglab:
            print(f"Coupling CH1/CH2: {settings[7]}, {settings[8]}")

        return settings

    def acq_start(self) -> None:
        """
        Starts the acquisition.
        """
        self.tx_txt("ACQ:START")
        self.check_error()

    def acq_stop(self) -> None:
        """
        Stops the acquisition.
        """
        self.tx_txt("ACQ:STOP")
        self.check_error()

    # Acq trigger
    def acq_trig_set(
        self,
        trig_lvl: float = 0,
        trig_delay: int = 0,
        trig_delay_ns: bool = False,
        trig_hyst: Optional[float] = None,
        ext_trig_deb_us: Optional[int] = None,
        ext_trig_lvl: Optional[float] = None,
        siglab: bool = False,
        input4: bool = False
    ) -> None:
        """
        Set the trigger parameters for the standard signal acquisition.
        One trigger is used for all acquisition channels.

        Parameters
        -----------

            trig_lvl (float, optional) :
                Trigger level in Volts. {-1, 1} Volts on LV gain or {-20, 20} Volts on HV gain.
                Defaults to 0.
            trig_delay (int, optional) :
                Trigger delay in samples (if trig_delay_ns = True, then the delay is in ns)
                Defaults to 0.
            trig_delay_ns (bool, optional) :
                Change the trigger delay to nanoseconds instead of samples.
                Defaults to False.
            trig_hyst (float, optional):
                Trigger hysteresis threshold value in Volts. 
                Defaults to None.
            ext_trig_deb_us (int, optional):
                External trigger debounce filter length in microseconds. Pulses shorter
                than the setting will not count as a triggering moment.
                Defaults to None.
            ext_trig_lvl (float, optional) :
                Set trigger external level in V.
                (Only SIGNALlab 250-12)
                Defaults to None.
            siglab (bool, optional) :
                Set to True if operating with SIGNALlab 250-12.
                Defaults to False.
            input4 (bool, optional) :
                Set to True if operating with STEMlab 125-14 4-Input.
                Defaults to False.

        The settings will work on any Red Pitaya board. If operating on SIGNALlab 250-12
        or STEMlab 125-14 4-Input change the bool value of the appropriate parameter to
        true (siglab, input4). This will change the available range of input parameters.
        """
        self._validate_acq_trig_params(trig_lvl, trig_delay, trig_hyst, ext_trig_deb_us, ext_trig_lvl, siglab, input4)

        if trig_delay_ns:
            self.tx_txt(f"ACQ:TRig:DLY:NS {trig_delay}")
        else:
            self.tx_txt(f"ACQ:TRig:DLY {trig_delay}")

        if trig_hyst is not None:
            self.tx_txt(f"ACQ:TRig:HYST {trig_hyst}")

        if ext_trig_deb_us is not None:
            self.tx_txt(f"ACQ:TRig:EXT:DEBouncer:US {ext_trig_deb_us}")

        self.tx_txt(f"ACQ:TRig:LEV {trig_lvl}")

        if siglab and ext_trig_lvl is not None:
            self.tx_txt(f"TRig:EXT:LEV {ext_trig_lvl}")

        self.check_error()

    def acq_get_trig_settings(self, siglab: bool = False) -> List[str | None]:
        """
        Retrieves the standard acquisition settings from Red Pitaya, prints them in console and returns
        them as an array with the following sequence:
        [trig_dly, trig_dly_ns, trig_lvl, trig_hyst, ext_trig_deb_us, ext_trig_lvl]

            Trig_dly        - Current trigger delay in samples
            Trig_dly_ns     - Current trigger delay in nanoseconds
            Trig_lvl        - Current triger level in Volts
            Trig_hyst       - Current trigger hysteresis threshold in Volts
            Ext_trig_deb_us - Current external trigger debounce filter value in microseconds.
            Ext_trig_lvl    - Current external trigger level in Volts (SIGNALlab only)

        Note:   External trigger level setting does not exist if siglab = False

        Parameters
        ----------
            siglab (bool, optional):
                Set to True if operating with SIGNALlab 250-12.
                Defaults to False.

        """
        settings = [
            self.txrx_txt("ACQ:TRig:DLY?"),
            self.txrx_txt("ACQ:TRig:DLY:NS?"),
            self.txrx_txt("ACQ:TRig:LEV?"),
            self.txrx_txt("ACQ:TRig:HYST?"),
            self.txrx_txt("ACQ:TRig:EXT:DEBouncer:US?")
        ]

        if siglab:
            settings.append(self.txrx_txt("TRig:EXT:LEV?"))

        self.check_error()

        #? Remove prints? Repace with logging?
        print(f"Trigger delay (samples): {settings[0]}")
        print(f"Trigger delay (ns): {settings[1]}")
        print(f"Trigger level (V): {settings[2]}")
        print(f"Trigger hysteresis (V): {settings[3]}")
        print(f"External trigger debouncer (us): {settings[4]}")

        if siglab:
            print(f"External trigger level (V): {settings[5]}")

        return settings

    def acq_trig_ext_hyst_set(
        self,
        trig_hyst: Optional[float] = None,
        ext_trig_deb_us: Optional[int] = None,
        ext_trig_lvl: Optional[float] = None,
        siglab: bool = False
    ) -> None:
        """
        Set the acquisition trigger parameters common for all channels.
        
        Parameters
        -----------

            trig_hyst (float, optional):
                Trigger hysteresis threshold value in Volts. 
                Defaults to None.
            ext_trig_deb_us (int, optional):
                External trigger debounce filter length in microseconds. Pulses shorter
                than the setting will not count as a triggering moment.
                Defaults to None.
            ext_trig_lvl (float, optional) :
                Set trigger external level in V.
                (Only SIGNALlab 250-12)
                Defaults to None.
            siglab (bool, optional) :
                Set to True if operating with SIGNALlab 250-12.
                Defaults to False.

        The settings will work on any Red Pitaya board. If operating on SIGNALlab 250-12
        change the bool value of the appropriate parameter to true (siglab).
        This will change the available range of input parameters.
        """
        self._validate_acq_trig_ext_hyst_params(trig_hyst, ext_trig_deb_us, ext_trig_lvl, siglab)

        if trig_hyst is not None:
            self.tx_txt(f"ACQ:TRig:HYST {trig_hyst}")

        if ext_trig_deb_us is not None:
            self.tx_txt(f"ACQ:TRig:EXT:DEBouncer:US {ext_trig_deb_us}")

        if siglab and ext_trig_lvl is not None:
            self.tx_txt(f"TRig:EXT:LEV {ext_trig_lvl}")
        self.check_error()

    # Misc
    def acq_set_units_format(
        self,
        units: Optional[Units] = None,
        data_format: Optional[DataFormat] = None
    ) -> None:
        """
        Set the units and format for the acquisition

        Parameters
        -----------

            units (str, optional) :
                The units in which the acquired data will be returned.
                Defaults to "VOLTS".
            data_format (str, optional) :
                The format in which the acquired data will be returned.
                Defaults to "ASCII".
        """
        self._validate_units_format(units, data_format)
        if units is not None:
            self.tx_txt(f"ACQ:DATA:Units {units.value}")
        if data_format is not None:
            self.tx_txt(f"ACQ:DATA:FORMAT {data_format.value}")

        self.check_error()

    # Split trigger mode
    def acq_split_enable(self) -> None:
        """
        Enables acquisition split trigger mode.
        """
        self.tx_txt("ACQ:SPLIT:TRig ON")
        self.check_error()

    def acq_split_disable(self) -> None:
        """
        Disables acquisition split trigger mode.
        """
        self.tx_txt("ACQ:SPLIT:TRig OFF")
        self.check_error()

    #TODO add get settings
    def acq_split_set(
        self,
        chan: int,
        dec: int = 1,
        averaging: bool = True,
        gain: Optional[Gain] = None,
        coupling: Optional[Coupling] = None,
        siglab: bool = False,
        input4: bool = False
    ) -> None:

        """
        Set the parameters for a specific acquisition channel using the split trigger
        signal acquisition mode. Each channel has its own trigger.

        Parameters
        -----------
            chan (int) :
                Input acquisition channel (1 or 2).
                (1,2,3, or 4 for STEMlab 125-14 4-Input).
            dec (int, optional) : 
                Decimation (1, 2, 4, 8, 16, 17, 18, ..., 65535, 65536)
                Defaults to 1.
            averaging (bool, optional) :
                Enable/disable averaging. When True, if decimation is higher than 1,
                each returned sample is the average of the taken samples. For example,
                if dec = 4, the returned sample will be the average of the 4 decimated
                samples.
                Defaults to True.
            gain (str, optional) :
                HV / LV - (High (1:20) or Low (1:1 attenuation)) 
                Refers to jumper settings on Red Pitaya fast analog inputs.
                (1:20 and 1:1 attenuator for SIGNALlab 250-12)
                Defaults to "None".
            coupling (str, optional) :
                AC / DC - coupling mode for fast analog inputs.
                (Only SIGNALlab 250-12)
                Defaults to "None".
            siglab (bool, optional) :
                Set to True if operating with SIGNALlab 250-12.
                Defaults to False.
            input4 (bool, optional) :
                Set to True if operating with STEMlab 125-14 4-Input.
                Defaults to False.

        The settings will work on any Red Pitaya board. If operating on SIGNALlab 250-12
        or STEMlab 125-14 4-Input change the bool value of the appropriate parameter to
        true (siglab, input4). This will change the available range of input parameters.
        """
        self._validate_acq_split_params(chan, dec, gain, coupling, siglab, input4)

        self.tx_txt(f"ACQ:DEC:Factor:CH{chan} {dec}")
        self.tx_txt(f"ACQ:AVG:CH{chan} {'ON' if averaging else 'OFF'}")
        if gain is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:GAIN {gain.value}")
        if siglab and coupling is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:COUP {coupling.value}")

        self.check_error()

    def acq_split_trig_set(
        self,
        chan: int,
        trig_lvl: float = 0,
        trig_delay: int = 0,
        trig_delay_ns: bool = False,
        input4: bool = False
    ) -> None:
        """
        Set the trigger parameters for the split trigger acquisition.
        Each channel uses a separate trigger.

        Parameters
        -----------
            chan (int) :
                Input acquisition channel (1 or 2).
                (1,2,3, or 4 for STEMlab 125-14 4-Input).
            trig_lvl (float, optional) :
                Trigger level in Volts. {-1, 1} Volts on LV gain or {-20, 20} Volts on HV gain.
                Defaults to 0.
            trig_delay (int, optional) :
                Trigger delay in samples (if trig_delay_ns = True, then the delay is in ns)
                Defaults to 0.
            trig_delay_ns (bool, optional) :
                Change the trigger delay to nanoseconds instead of samples.
                Defaults to False.
            input4 (bool, optional) :
                Set to True if operating with STEMlab 125-14 4-Input.
                Defaults to False.

        The settings will work on any Red Pitaya board. If operating on STEMlab 125-14 4-Input
        change the bool value of the appropriate parameter to true (input4).
        This will change the available range of input parameters.
        """
        self._validate_acq_split_trig_params(chan, trig_lvl, trig_delay, trig_delay_ns, input4)

        if trig_delay_ns:
            self.tx_txt(f"ACQ:TRig:DLY:NS:CH{chan} {trig_delay}")
        else:
            self.tx_txt(f"ACQ:TRig:DLY:CH{chan} {trig_delay}")

        self.tx_txt(f"ACQ:TRig:LEV:CH{chan} {trig_lvl}")
        self.check_error()

    # Get data from RP
    def acq_data(
        self,
        chan: int,
        start: Optional[int] = None,
        end: Optional[int] = None,
        num_samples: Optional[int] = None,
        old: bool = False,
        last: bool = False,
        trig_pos: Optional[DataTriggerPosition] = None,
        input4: bool = False
    ) -> np.ndarray:
        """
        Returns the acquired data on a channel from the Red Pitaya, with the following options (for a specific channel):
            - only channel       => returns the whole buffer
            - start and end      => returns the samples between them
            - start and n        => returns 'n' samples from the start position
            - old and n          => returns 'n' oldest samples in the buffer
            - lat and n          => returns 'n' latest samples in the buffer
            - trig_pos and n     => returns 'n' samples around trigger position (depends on setting)

        Parameters
        ----------
            chan (int) :
                Input acquisition channel (1 or 2).
                (1,2,3, or 4 for STEMlab 125-14 4-Input).
            start (int, optional):
                Start position of acquired data in the buffer {0,1,...16384}
                Defaults to None.
            end (int, optional):
                End position of acquired data in the buffer {0,1,...16384}
                Defaults to None.
            num_samples (int, optional):
                Number of samples read (== `n`).
                Defaults to None.
            old (bool, optional):
                Read oldest samples in the buffer.
                Defaults to False.
            last (bool, optional):
                Read latest samples in the buffer.
                Defaults to False.
            trig_pos (str, optional):
                Read samples around trigger position:
                    - `PRE_TRIG` - before triggering moment (includes trigger sample)
                    - `POST_TRIG` - after triggering moment (includes trigger sample)
                    - `PRE_POST_TRIG` - before and after triggering moment (includes trigger sample)
                                        2*`n`+ 1 samples.
                Defaults to None.
            input4 (bool, optional) :
                Set to True if operating with STEMlab 125-14 4-Input.
                Defaults to False.

        Returns
        -------
            np.ndarray:
                Numpy array with captured data.
        """
        self._validate_acq_data_params(chan, start, end, num_samples, old, last, trig_pos, input4)

        # Determine the output data
        if start is not None and end is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:DATA:STArt:End? {start},{end}")
        elif start is not None and num_samples is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:DATA:STArt:N? {start},{num_samples}")
        elif old and num_samples is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:DATA:Old:N? {num_samples}")
        elif last and num_samples is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:DATA:LATest:N? {num_samples}")
        elif trig_pos is not None and num_samples is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:DATA:TRig? {num_samples},{trig_pos.value}")
        else:
            self.tx_txt(f"ACQ:SOUR{chan}:DATA?")

        # Get data type from Red Pitaya
        units = self.txrx_txt('ACQ:DATA:Units?')
        data_format = self.txrx_txt("ACQ:DATA:FORMAT?")
        self.check_error()

        #! Check if data_format is correct
        # Convert data
        if data_format == "BIN":
            buff_byte = self.rx_arb()
            if units == "VOLTS":
                buff = np.frombuffer(buff_byte, dtype='>f4')
                #buff = [struct.unpack('!f',bytearray(buff_byte[i:i+4]))[0] for i in range(0, len(buff_byte), 4)]
            elif units == "RAW":
                buff = np.frombuffer(buff_byte, dtype='>i2')
                #buff = [struct.unpack('!h',bytearray(buff_byte[i:i+2]))[0] for i in range(0, len(buff_byte), 2)]
        else:
            buff_string = self.rx_txt().strip('{}\n\r').replace("  ", "").split(',')
            buff = np.array(buff_string).astype(np.float64)
        self.check_error()

        return buff

    # Validations
    def _validate_acq_set_params(
        self,
        dec: int,
        units: Optional[Units],
        data_format: Optional[DataFormat],
        gain: Optional[List[Gain]],
        coupling: Optional[List[Coupling]],
        siglab: bool,
        input4: bool
    ) -> None:
        """
        Validate parameters for acq_set function.
        """
        dec_fact_list = [3, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]
        gain_list = [e.value for e in Gain]
        coupling_list = [e.value for e in Coupling]
        units_list = [e.value for e in Units]
        format_list = [e.value for e in DataFormat]

        assert (dec not in dec_fact_list) and (16 <= dec <= 65536), "Decimation factor out of range [1,2,4,8,16,17,18,...,65536]"
        if units is not None:
            assert units.value in units_list, f"{units.value} is not a defined unit"
        if data_format is not None:
            assert data_format.value in format_list, f"{data_format.value} is not a defined format"
        if gain is not None:
            for g in gain:
                assert g.value in gain_list, f"{g.value} is not a defined gain"
        if siglab and coupling is not None:
            for c in coupling:
                assert c.value in coupling_list, f"{c.value} is not a defined coupling"
        self._validate_board(siglab, input4)

    def _validate_units_format(
        self,
        units: Optional[Units],
        data_format: Optional[DataFormat]
    ) -> None:
        """
        Validate parameters for acq_set_units_format function.
        """
        units_list = [e.value for e in Units]
        format_list = [e.value for e in DataFormat]

        if units is not None:
            assert units.value in units_list, f"{units.value} is not a defined unit"
        if data_format is not None:
            assert data_format.value in format_list, f"{data_format.value} is not a defined format"

    def _validate_acq_trig_params(
        self,
        trig_lvl: float,
        trig_delay: int,
        trig_hyst: Optional[float],
        ext_trig_deb_us: Optional[int],
        ext_trig_lvl: Optional[float],
        siglab: bool,
        input4: bool
    ) -> None:
        """
        Validate parameters for acq_trig_set function.
        """
        trig_lvl_lim = 20.0 if any(self.txrx_txt(f"ACQ:SOUR{i+1}:GAIN?").upper() == "HV" for i in range(4 if input4 else 2)) else 1.0
        ext_trig_lvl_limit = 5.0

        assert abs(trig_lvl) <= trig_lvl_lim, f"Trigger level out of range {-trig_lvl_lim, trig_lvl_lim} V"
        assert trig_delay >= 0, "Trigger delay cannot be less than 0"
        if trig_hyst is not None:
            assert trig_hyst >= 0, "Trigger hysteresis cannot be negative"
        if siglab and ext_trig_lvl is not None:
            assert abs(ext_trig_lvl) <= ext_trig_lvl_limit, f"External trigger level out of range {-ext_trig_lvl_limit, ext_trig_lvl_limit} V"
        if ext_trig_deb_us is not None:
            assert ext_trig_deb_us >= 1, "External trigger debounce filter value is out of range. The minimal value is 1 microsecond"
        assert not (siglab and input4), "Please select only one board option. 'siglab' and 'input4' cannot be true at the same time."
        self._validate_board(siglab, input4)

    def _validate_acq_trig_ext_hyst_params(
        self,
        trig_hyst: Optional[float],
        ext_trig_deb_us: Optional[int],
        ext_trig_lvl: Optional[float],
        siglab: bool
    ) -> None:
        """
        Validate parameters for acq_trig_ext_hyst_set function.
        """
        ext_trig_lvl_limit = 5.0

        if trig_hyst is not None:
            assert trig_hyst >= 0, "Trigger hysteresis cannot be negative"
        if siglab and ext_trig_lvl is not None:
            assert abs(ext_trig_lvl) <= ext_trig_lvl_limit, f"External trigger level out of range {-ext_trig_lvl_limit, ext_trig_lvl_limit} V"
        if ext_trig_deb_us is not None:
            assert ext_trig_deb_us >= 1, "External trigger debounce filter value is out of range. The minimal value is 1 microsecond"

    def _validate_acq_split_params(
        self,
        chan: int,
        dec: int,
        gain: Optional[Gain],
        coupling: Optional[Coupling],
        siglab: bool,
        input4: bool
    ) -> None:
        """
        Validate parameters for acq_split_set function.
        """
        dec_fact_list = [3, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]
        gain_list = [e.value for e in Gain]
        coupling_list = [e.value for e in Coupling]

        n = 4 if input4 else 2

        assert chan <= n, f"Channel {chan} out of range for the current Red Pitaya board"
        assert (dec not in dec_fact_list) and (16 <= dec <= 65536), "Decimation factor out of range [1,2,4,8,16,17,18,...,65536]"
        if gain is not None:
            assert gain.value in gain_list, f"{gain.value} is not a defined gain"
        if siglab and coupling is not None:
            assert coupling.value in coupling_list, f"{coupling.value} is not a defined coupling"
        assert not (siglab and input4), "Please select only one board option. 'siglab' and 'input4' cannot be true at the same time."

    def _validate_acq_split_trig_params(
        self,
        chan: int,
        trig_lvl: float,
        trig_delay: int,
        input4: bool
    ) -> None:
        """
        Validate parameters for acq_split_trig_set function.
        """
        n = 4 if input4 else 2
        gain_lvl = "LV"
        trig_lvl_lim = 1.0

        assert chan <= n, f"Channel {chan} out of range for the current Red Pitaya board"

        gain = self.txrx_txt(f"ACQ:SOUR{chan}:GAIN?")
        if gain.upper() == "HV":
            trig_lvl_lim = 20.0
            gain_lvl = "HV"

        assert abs(trig_lvl) <= trig_lvl_lim, f"Trigger level out of range {-trig_lvl_lim, trig_lvl_lim} V for gain {gain_lvl}"
        assert trig_delay >= 0, "Trigger delay cannot be less than 0"

    def _validate_acq_data_params(
        self,
        chan: int,
        start: Optional[int],
        end: Optional[int],
        num_samples: Optional[int],
        old: bool,
        last: bool,
        trig_pos: Optional[DataTriggerPosition],
        input4: bool
    ) -> None:
        """
        Validate parameters for acq_data function.
        """
        n = 4 if input4 else 2
        low_lim = 0
        up_lim = 16384

        assert chan <= n, f"Channel {chan} out of range for the current Red Pitaya board"
        assert not (old and last), "Please select only one. 'old' and 'last' cannot be True at the same time."
        if start is not None:
            assert low_lim <= start <= up_lim, f"Start position out of range {low_lim, up_lim}"
        if end is not None:
            assert low_lim <= end <= up_lim, f"End position out of range {low_lim, up_lim}"
        if num_samples is not None:
            assert low_lim <= num_samples <= up_lim, f"Sample number out of range {low_lim, up_lim}"
            if trig_pos is not None:
                assert trig_pos in DataTriggerPosition, f"Trigger position value {trig_pos} is not defined"
                if trig_pos == DataTriggerPosition.PRE_POST_TRIG:
                    assert num_samples * 2 + 1 <= up_lim, f"Sample number is too big for {trig_pos.value} setting. This mode returns num_samples*2 +1 data samples."

    def _validate_board(self, siglab: bool, input4: bool) -> None:
        """
        Validate board model.
        """
        assert not(siglab and input4), "Please select only one board option. 'siglab' and 'input4' cannot be true at the same time."

    #! Check with Copilot
    ### UART ###

    def uart_set(
        self,
        speed: int = 9600,
        bits: UartBits = UartBits.CS8,
        parity: UartParity = UartParity.NONE,
        stop: int = 1,
        timeout: int = 0
    ) -> None:
        """
        Configures the provided settings for UART.

        Args:
            speed (int, optional): Baud rate/speed of UART connection (bits per second). Defaults to 9600.
            bits (str, optional): Character size in bits (CS6, CS7, CS8). Defaults to "CS8".
            parity (str, optional): Parity (NONE, EVEN, ODD, MARK, SPACE). Defaults to "NONE".
            stop (int, optional): Number of stop bits (1 or 2). Defaults to 1.
            timeout (int, optional): Timeout for reading from UART (in 1/10 of seconds) {0,...255}. Defaults to 0.
        """
        self._validate_uart_params(speed, bits, parity, stop, timeout)

        self.tx_txt("UART:INIT")
        self.tx_txt(f"UART:SPEED {speed}")
        self.tx_txt(f"UART:BITS {bits.value}")
        self.tx_txt(f"UART:STOPB STOP{stop}")
        self.tx_txt(f"UART:PARITY {parity.value}")
        self.tx_txt(f"UART:TIMEOUT {timeout}")

    def uart_get_settings(self) -> List[str | None]:
        """
        Retrieves the settings from Red Pitaya, prints them in console and returns
        them as an array with the following sequence:
        [speed, databits, stopbits, parity, timeout]
        """
        settings = [
            self.txrx_txt("UART:SPEED?"),
            self.txrx_txt("UART:BITS?"),
            self.txrx_txt("UART:STOPB?"),
            self.txrx_txt("UART:PARITY?"),
            self.txrx_txt("UART:TIMEOUT?")
        ]
        #? Remove prints? Repace with logging?
        print(f"Baudrate/Speed: {settings[0]}")
        print(f"Databits: {settings[1]}")
        print(f"Stopbits: {settings[2]}")
        print(f"Parity: {settings[3]}")
        print(f"Timeout (0.1 sec): {settings[4]}")

        return settings

    def uart_write_string(
        self,
        string: str,
        word_length: bool = False
    ) -> None:
        """
        Sends a string of characters through UART.
        """
        # Set the code depending on word length
        code = "ascii" if word_length else "utf-8"
        arr = ',#H'.join(format(x, 'X') for x in bytearray(string, code))
        # Send in hexa format
        self.tx_txt(f"UART:WRITE{len(string)} #H{arr}")

    def uart_read_string(
        self,
        length: int
    ) -> str:
        """
        Reads a string of data from UART and decodes it from ASCII to string.
        """
        assert length > 0, "Length must be greater than 0."

        self.tx_txt(f"UART:READ{length}?")
        res = self.rx_txt().strip('{}\n\r').replace("  ", "").split(',')
        string = "".join(chr(int(x)) for x in res)  # int(x).decode("utf8")

        return string

    # Validate
    def _validate_uart_params(
        self,
        speed: int,
        bits: UartBits,
        parity: UartParity,
        stop: int,
        timeout: int
    ) -> None:
        """
        Validate parameters for uart_set function.
        """
        speed_list = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400, 576000, 921000, 1000000, 1152000, 1500000, 2000000, 2500000, 3000000, 3500000, 4000000]
        bits_list = [e.value for e in UartBits]
        parity_list = [e.value for e in UartParity]

        assert speed in speed_list, f"{speed} is not a defined speed for UART connection. Please check the speed table."
        assert bits.value in bits_list, f"{bits.value} is not a defined character size."
        assert parity.value in parity_list, f"{parity.value} is not a defined parity."
        assert stop in (1, 2), "The number of stop bits can only be 1 or 2"
        assert 0 <= timeout <= 255, f"Timeout {timeout} is out of range [0, 255]"

    ### SPI ###

    def spi_set(
        self,
        spi_mode: str = None,
        cs_mode: str = None,
        speed: int = None,
        word_len: int = None
    ) -> None:
        """
        Configures the provided settings for SPI.

        Args:
            spi_mode (str, optional): Sets the mode for SPI; - LISL (Low Idle level, Sample Leading edge)
                                                             - LIST (Low Idle level, Sample Trailing edge)
                                                             - HISL (High Idle level, Sample Leading edge)
                                                             - HIST (High Idle level, Sample Trailing edge)
                                                        Defaults to LISL.
            cs_mode (str, optional): Sets the mode for CS: - NORMAL (After message transmission, CS => HIGH)
                                                           - HIGH (After message transmission, CS => LOW)
                                                        Defaults to NORMAL.
            speed (int, optional): Sets the speed of the SPI connection. Defaults to 5e7.
            word_len (int, optional): Character size in bits (CS6, CS7, CS8). Defaults to "CS8".
        """

        # Constants
        speed_max_limit = 100e6
        speed_min_limit = 1
        cs_mode_list = ["NORMAL","HIGH"]
        #order_list = ["MSB","LSB"]
        spi_mode_list = ["LISL","LIST","HISL","HIST"]
        bits_min_limit = 7


        # Input Limits Check

        try:
            assert spi_mode.upper() in spi_mode_list
        except AssertionError as spi_mode_err:
            raise ValueError(f"{spi_mode} is not a defined SPI mode.") from spi_mode_err

        try:
            assert cs_mode.upper() in cs_mode_list
        except AssertionError as cs_err:
            raise ValueError(f"{cs_mode} is not a defined CS mode.") from cs_err

        try:
            assert speed_min_limit <= speed <= speed_max_limit
        except AssertionError as speed_err:
            raise ValueError(f"{speed} is out of range [{speed_min_limit},{speed_max_limit}].") from speed_err

        try:
            assert word_len >= bits_min_limit
        except AssertionError as bits_err:
            raise ValueError(f"Word length must be greater than {bits_min_limit}. Current word length: {word_len}") from bits_err


        # Configuring SPI

        self.tx_txt(f"SPI:SETtings:MODE {spi_mode.upper()}")
        self.tx_txt(f"SPI:SETtings:CSMODE {cs_mode.upper()}")
        self.tx_txt(f"SPI:SETtings:SPEED {speed}")
        self.tx_txt(f"SPI:SETtings:WORD {word_len}")

        self.tx_txt("SPI:SETtings:SET")
        print("SPI is configured")

    def spi_get_settings(
        self
    ) -> List[str | None]:
        """
        Retrieves the SPI settings from Red Pitaya, prints them in console and returns
        them as an array with the following sequence:
        [mode, csmode, speed, word_len, msg_size]
        """
        self.tx_txt("SPI:SETtings:GET")
        settings = [
            self.txrx_txt("SPI:SETtings:MODE?"),
            self.txrx_txt("SPI:SETtings:CSMODE?"),
            self.txrx_txt("SPI:SETtings:SPEED?"),
            self.txrx_txt("SPI:SETtings:WORD?"),
            self.txrx_txt("SPI:MSG:SIZE?")
        ]

        print(f"SPI mode: {settings[0]}")
        print(f"CS mode: {settings[1]}")
        print(f"Speed: {settings[2]}")
        print(f"Word length: {settings[3]}")
        print(f"Message queue length: {settings[4]}")

        return settings

    #TODO add spi_write()
    #TODO add spi_read()

    ### I2C ###

    #TODO add i2c_set()
    #TODO add i2c_get_settings()
    #TODO add i2c_write() - protocol IOctl Smbus
    #TODO add i2c_read() - protocol IOctl Smbus

    ### CAN ###

    #TODO add can_set(), can_get_settings(), can_write(), can_read()

    ### DMA ###

    #TODO add dma_set(), dma_get_settings()

    ### LCR ###

    #TODO add LCR meter commands

    ### MISCELANUOUS ###

    #TODO add status_led()



    ####################################################
    ###            IEEE Mandated Commands            ###
    ####################################################
    #
    #! Functions in this section should not be modified as they take care of the communication between Red Pitaya and the computer
    #

    # IEEE Mandated Commands

    def cls(self):
        """Clear Status Command"""
        return self.tx_txt('*CLS')

    def ese(self, value: int):
        """Standard Event Status Enable Command"""
        return self.tx_txt(f'*ESE {value}')

    def ese_q(self):
        """Standard Event Status Enable Query"""
        return self.txrx_txt('*ESE?')

    def esr_q(self):
        """Standard Event Status Register Query"""
        return self.txrx_txt('*ESR?')

    def idn_q(self):
        """Identification Query"""
        return self.txrx_txt('*IDN?')

    def opc(self):
        """Operation Complete Command"""
        return self.tx_txt('*OPC')

    def opc_q(self):
        """Operation Complete Query"""
        return self.txrx_txt('*OPC?')

    def rst(self):
        """Reset Command"""
        return self.tx_txt('*RST')

    def sre(self, value: int):
        """Service Request Enable Command"""
        return self.tx_txt('*SRE {value}')

    def sre_q(self):
        """Service Request Enable Query"""
        return self.txrx_txt('*SRE?')

    def stb_q(self):
        """Read Status Byte Query"""
        return self.txrx_txt('*STB?')

    # :SYSTem

    def err_c(self):
        """Error count."""
        return self.txrx_txt('SYST:ERR:COUN?')

    def err_n(self):
        """Error next."""
        return self.txrx_txt('SYST:ERR:NEXT?')
