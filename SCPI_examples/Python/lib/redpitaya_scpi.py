"""
Provides SCPI access to Red Pitaya from host computer.

!!! LATEST IN DEV !!! - 27.5.2026
"""

import math
import re
import socket
import time
import warnings
from enum import Enum
from typing import List, Optional, Tuple, Union
import numpy as np
import struct

__author__ = "Luka Golinar, Iztok Jeras, Miha Gjura"
__copyright__ = "Copyright 2026, Red Pitaya"
__version__ = "3.0.0"
__OS_version__ = "3.00 and higher"

#TODO - is dual return list type even necessary? Maybe just skip the None values


class SCPIError(Exception):
    """Custom exception for SCPI communication errors."""
    def __init__(self, message: str, error_code: Optional[int] = None):
        super().__init__(message)
        self.error_code = error_code

class SCPICriticalError(SCPIError):
    """Exception raised for critical SCPI errors (error code > 9500)."""
    pass


class BoardModel(Enum):
    """Red Pitaya board model. Pass to functions that have board-specific behaviour."""
    STEMLAB_125_14                  = "STEMLAB_125_14"
    STEMLAB_125_14_4INPUT           = "STEMLAB_125_14_4INPUT"
    STEMLAB_125_14_GEN2             = "STEMLAB_125_14_GEN2"
    STEMLAB_125_14_PRO_Z7020_GEN2   = "STEMLAB_125_14_PRO_Z7020_GEN2"
    STEMLAB_125_14_TI               = "STEMLAB_125_14_TI"
    STEMLAB_65_16_TI                = "STEMLAB_65_16_TI"
    SDRLAB_122_16                   = "SDRLAB_122_16"
    SIGNALLAB_250_12                = "SIGNALLAB_250_12"

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

class GenLoad(Enum):
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

class AcqTrigSource(Enum):
    """Trigger sources for acquisition (ACQ:TRig command)."""
    DISABLED = "DISABLED"
    # Analog channel — positive / negative / any edge
    CH1_PE   = "CH1_PE"
    CH1_NE   = "CH1_NE"
    CH1_AE   = "CH1_AE"   # Any edge
    CH2_PE   = "CH2_PE"
    CH2_NE   = "CH2_NE"
    CH2_AE   = "CH2_AE"   # Any edge
    # STEMlab 125-14 4-Input only
    CH3_PE   = "CH3_PE"
    CH3_NE   = "CH3_NE"
    CH3_AE   = "CH3_AE"   # Any edge
    CH4_PE   = "CH4_PE"
    CH4_NE   = "CH4_NE"
    CH4_AE   = "CH4_AE"   # Any edge
    # Generator / external
    AWG_PE   = "AWG_PE"
    AWG_NE   = "AWG_NE"
    EXT_PE   = "EXT_PE"
    EXT_NE   = "EXT_NE"
    # Immediately
    NOW      = "NOW"

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

class ByteOrder(Enum):
    """Byte order settings for binary data."""
    LEND = "LEND"
    BEND = "BEND"

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

class SPIDataType(Enum):
    """SPI data type settings."""
    BIN = "BIN"
    OCT = "OCT"
    DEC = "DEC"
    HEX = "HEX"
    
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

class DaisyMode(Enum):
    """Daisy chain synchronisation method."""
    X_CHANNEL    = "X_CHANNEL"     # X-channel system 1.0 (SATA-based, STEMlab 125-14 only)
    X_CHANNEL_V2 = "X_CHANNEL_V2"  # X-channel system 2.0 (formerly Click Shield synchronisation)

class DaisyTrigMode(Enum):
    """Trigger source to be shared."""
    ADC = "ADC"
    DAC = "DAC"



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
        self._socket: Optional[socket.socket] = None

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if timeout is not None:
                self._socket.settimeout(timeout)

            self._socket.connect((host, port))

        except socket.error as e:
            if self._socket is not None:
                try:
                    self._socket.close()
                except OSError:
                    pass
                self._socket = None
            raise ConnectionError('SCPI >> connect({!s:s}:{:d}) failed: {!s:s}'.format(host, port, e)) from e

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Cleanup socket connection on object destruction."""
        try:
            self.close()
        except (OSError, AttributeError):
            pass  # Ignore cleanup errors

    @property
    def is_connected(self) -> bool:
        """Check if socket is connected."""
        return self._socket is not None

    def close(self):
        """Close IP connection."""
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass  # Ignore close errors
            finally:
                self._socket = None

    def _ensure_connected(self):
        """Ensure socket is connected, raise exception if not."""
        if self._socket is None:
            raise ConnectionError("Not connected to Red Pitaya device")

    def rx_txt(self, chunksize: int = 4096) -> str:
        """Receive text string and return it after removing the delimiter.
        
        Args:
            chunksize: Size of chunks to receive (default: 4096)
            
        Returns:
            Received text string without delimiter
            
        Raises:
            ConnectionError: If not connected to device or connection closed
            socket.error: If communication fails
        """
        self._ensure_connected()
        
        msg = ''
        try:
            while True:
                data = self._socket.recv(chunksize)  # type: ignore
                if not data:  # Connection closed by peer
                    raise ConnectionError("Socket connection closed by peer")
                
                chunk = data.decode('utf-8')
                msg += chunk
                if len(msg) >= 2 and msg[-2:] == self.delimiter:
                    return msg[:-2]
        except socket.error as e:
            raise ConnectionError(f"Error receiving text: {e}") from e

    def rx_txt_check_error(self, chunksize: int = 4096, stop: bool = True) -> str:
        """Receive text string and return it after removing the delimiter.
        Check for error."""
        msg = self.rx_txt(chunksize)
        self.check_error(stop)
        return msg

    def rx_arb(self) -> Union[bytes, bool]:
        """Receive binary data from SCPI server.
        
        Returns:
            Binary data or False if failed
            
        Raises:
            ConnectionError: If not connected to device
        """
        self._ensure_connected()
        
        try:
            # Read header byte '#'
            data = b''
            while len(data) != 1:
                chunk = self._socket.recv(1)  # type: ignore
                if not chunk:
                    raise ConnectionError("Connection closed while reading header")
                data = chunk
            if data != b'#':
                return False
            
            # Read number of length digits
            data = b''
            while len(data) != 1:
                chunk = self._socket.recv(1)  # type: ignore
                if not chunk:
                    raise ConnectionError("Connection closed while reading length specification")
                data = chunk
            numOfNumBytes = int(data)
            if numOfNumBytes <= 0:
                return False
            
            # Read length
            data = b''
            while len(data) != numOfNumBytes:
                chunk = self._socket.recv(1)  # type: ignore
                if not chunk:
                    raise ConnectionError("Connection closed while reading data length")
                data += chunk
            numOfBytes = int(data)
            
            # Read actual data
            data = b''
            while len(data) < numOfBytes:
                r_size = min(numOfBytes - len(data), 4096 * 1024)
                chunk = self._socket.recv(r_size)  # type: ignore
                if not chunk:
                    raise ConnectionError("Connection closed while reading data")
                data += chunk

            # Receive trailing \r\n
            try:
                self._socket.recv(2)  # type: ignore
            except socket.error:
                pass  # Don't fail if trailing bytes are missing

            return data
            
        except (socket.error, ValueError) as e:
            raise ConnectionError(f"Error receiving binary data: {e}") from e

    def rx_arb_check_error(self, stop: bool = True) -> Union[bytes, bool]:
        """ Recieve binary data from scpi server. Check for error."""
        data = self.rx_arb()
        self.check_error(stop)
        return data

    def tx_txt(self, msg: str) -> None:
        """Send text string with delimiter appended.
        
        Args:
            msg: Text message to send
            
        Raises:
            ConnectionError: If not connected to device or communication fails
        """
        self._ensure_connected()
        
        try:
            self._socket.sendall((msg + self.delimiter).encode('utf-8'))  # type: ignore
        except socket.error as e:
            raise ConnectionError(f"Error sending text: {e}") from e

    def tx_txt_check_error(self, msg: str, stop: bool= True):
        """Send text string ending and append delimiter. Check for error."""
        self.tx_txt(msg)
        self.check_error(stop)

    def txrx_txt(self, msg: str) -> str:
        """Send/receive text string."""
        self.tx_txt(msg)
        return self.rx_txt()

    def check_error(self, stop: bool = True) -> None:
        """Check for SCPI errors and optionally raise exception on critical errors.
        
        Args:
            stop: Whether to raise exception on critical errors (code > 9500)
            
        Raises:
            SCPICriticalError: On critical errors if stop=True
            ConnectionError: If communication fails
        """
        try:
            stb_result = self.stb_q()
            if stb_result is None:
                return
                
            res = int(stb_result)
            if res & 0x4:  # Error queue not empty
                while True:
                    err = self.err_n()
                    if err is None:
                        break
                        
                    if err.startswith('0,'):
                        break
                        
                    print(f"SCPI Error: {err}")
                    
                    try:
                        error_parts = err.split(",")
                        if len(error_parts) > 0 and stop:
                            error_code = int(error_parts[0])
                            if error_code > 9500:
                                raise SCPICriticalError(f"Critical SCPI error {error_code}: {err}", error_code)
                    except (ValueError, IndexError):
                        pass  # Could not parse error code, continue
                        
        except (ConnectionError, socket.error) as e:
            if stop:
                raise ConnectionError(f"Error during error checking: {e}") from e


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
        """Returns Red Pitaya board ID, model name, and OS version.

        Returns:
            List[str]: ``[board_id, board_name, os_version]``.
        """
        settings = [
            self.txrx_txt('SYSTem:BRD:ID?'),
            self.txrx_txt('SYSTem:BRD:Name?'),
            self.txrx_txt('SYSTem:VERSion?'),
        ]
        self.check_error()
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
        mode: DaisyMode,
        trig_mode: Optional[DaisyTrigMode] = None
    ) -> None:
        """
        Configure the daisy chain synchronisation mode for Red Pitaya.

        Args:
            mode (DaisyMode): Synchronisation method.
                - ``DaisyMode.X_CHANNEL``    — X-channel system 1.0 (SATA-based clock + trigger
                                               sync). Only available on STEMlab 125-14.
                - ``DaisyMode.X_CHANNEL_V2`` — X-channel system 2.0 (formerly Click Shield
                                               synchronisation). Available on all boards.
            trig_mode (DaisyTrigMode, optional): Trigger source shared over DIO0_N
                (``ADC`` or ``DAC``). Applies to ``DaisyMode.X_CHANNEL_V2`` only.
                Defaults to None.
        """
        if mode == DaisyMode.X_CHANNEL:
            self.tx_txt("DAISY:SYNC:CLK ON")
            self.tx_txt("DAISY:SYNC:TRIG ON")
        elif mode == DaisyMode.X_CHANNEL_V2:
            self.tx_txt("DAISY:TRig:Out:ENable ON")
            if trig_mode is not None:
                self.tx_txt(f"DAISY:TRig:Out:SOUR {trig_mode.value}")
        self.check_error()

    def daisy_get_settings(
        self,
        board: BoardModel = BoardModel.STEMLAB_125_14
    ) -> List[str]:
        """
        Returns the current Daisy chain settings.

        For ``BoardModel.STEMLAB_125_14`` (X-channel 1.0 capable), returns:
            [clk_sync, trig_sync, trig_out_en, trig_out_sour]
        For all other boards (X-channel 2.0 only), returns:
            [trig_out_en, trig_out_sour]

        Args:
            board (BoardModel, optional): Board model. Defaults to STEMLAB_125_14.

        Returns:
            List[str]: Daisy chain settings.
        """
        settings = []

        if board == BoardModel.STEMLAB_125_14:
            settings.append(self.txrx_txt("DAISY:SYNC:CLK?"))
            settings.append(self.txrx_txt("DAISY:SYNC:TRIG?"))
            settings.append(self.txrx_txt("DAISY:TRig:Out:ENable?"))
            settings.append(self.txrx_txt("DAISY:TRig:Out:SOUR?"))
        else:
            settings.append(self.txrx_txt("DAISY:TRig:Out:ENable?"))
            settings.append(self.txrx_txt("DAISY:TRig:Out:SOUR?"))

        self.check_error()
        return settings


    ### PLL ###

    def pll_set(
        self,
        enable: bool
    ) -> None:
        """
        Enables or disables Phase Locked Loop control on SIGNALlab 250-12.
        Syncs the board with the 10 MHz reference clock on the rear SMA connector.

        Note:
            SIGNALlab 250-12 only. Calling on other board models will result in an
            SCPI error or no response from the device.

        Args:
            enable (bool): True to enable PLL, False to disable.
        """
        self.tx_txt(f"RP:PLL:ENable {'ON' if enable else 'OFF'}")
        self.check_error()

    def pll_get_state(
        self
    ) -> List[str]:
        """
        Returns whether PLL is enabled and whether it is locked to the 10 MHz
        reference clock on the rear SMA connector.

        Note:
            SIGNALlab 250-12 only. Calling on other board models may result in an
            SCPI error or no response from the device.

        Returns:
            List[str]: [pll_enable, pll_state]
        """
        pll_enable = self.txrx_txt("RP:PLL:ENable?")
        pll_state  = self.txrx_txt("RP:PLL:STATE?")
        self.check_error()
        return [pll_enable, pll_state]


    ### GENERATOR ###
    #TODO check SCPI commands

    # Continuous
    def gen_set(
        self,
        chan: int,
        func: Waveform = Waveform.SINE,
        ampl: float = 1,
        freq: float = 1000,
        offset: Optional[float] = None,
        phase: Optional[float] = None,
        dcyc: Optional[float] = None,
        data: Optional[np.ndarray] = None,
        load: Optional[GenLoad] = None,
        board: BoardModel = BoardModel.STEMLAB_125_14
    ) -> None:
        """
        Set the waveform parameters for signal generator on one channel.

        Use :meth:`gen_trig_set` to configure the trigger source and
        external trigger settings.

        Args:
            chan (int):
                Output channel (either 1 or 2).
            func (Waveform, optional):
                Waveform of the signal (SINE, SQUARE, TRIANGLE, SAWU,
                SAWD, PWM, ARBITRARY, DC, DC_NEG).
                Defaults to ``Waveform.SINE``.
            ampl (float, optional):
                Amplitude of signal {-1, 1} V. {-5, 5} V for SIGNALlab 250-12.
                Defaults to 1.
            freq (float, optional):
                Frequency of signal. Not relevant if ``func`` is DC or DC_NEG.
                Defaults to 1000.
            offset (float, optional):
                Signal offset {-1, 1} V. {-5, 5} V for SIGNALlab 250-12.
                Defaults to None (0 V).
            phase (float, optional):
                Phase of signal {-360, 360} degrees.
                Defaults to None (0°).
            dcyc (float, optional):
                Duty cycle {0, 1} where 1 corresponds to 100%. PWM waveform only.
                Defaults to None (0.5).
            data (ndarray, optional):
                Numpy array of max 16384 floats in range {-1, 1} (or {-5, 5} for
                SIGNALlab 250-12). Used when ``func`` is ``Waveform.ARBITRARY``.
                Defaults to None.
            load (GenLoad, optional):
                Expected generator load (INF or L50).
                SIGNALlab 250-12 and STEMlab 125-14 Gen2 only.
                Defaults to None (INF).
            board (BoardModel, optional):
                Board model. Defaults to ``BoardModel.STEMLAB_125_14``.
        """
        self._validate_gen_set_params(chan, func, ampl, freq, offset, phase, dcyc, data, load, board)

        # Load must be set before amplitude
        if board in (BoardModel.SIGNALLAB_250_12, BoardModel.STEMLAB_125_14_GEN2, BoardModel.STEMLAB_125_14_PRO_Z7020_GEN2):
            if load is not None:
                self.tx_txt(f"SOUR{chan}:LOAD {load.value}")

        self.tx_txt(f"SOUR{chan}:FUNC {func.value}")
        self.tx_txt(f"SOUR{chan}:VOLT {ampl}")

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

        self.check_error()

    def gen_trig_set(
        self,
        chan: int,
        trig_sour: Optional[TriggerSource] = None,
        ext_trig_deb_us: Optional[int] = None,
        ext_trig_lev: Optional[float] = None,
        board: BoardModel = BoardModel.STEMLAB_125_14
    ) -> None:
        """
        Set the trigger parameters for signal generator on one channel.

        Use :meth:`gen_set` to configure the waveform shape and output
        settings.

        Args:
            chan (int):
                Output channel (either 1 or 2).
            trig_sour (TriggerSource, optional):
                Trigger source (EXT_PE, EXT_NE, INT).
                Defaults to None (no change).
            ext_trig_deb_us (int, optional):
                External trigger debounce filter length in microseconds.
                Shared across both channels.
                Defaults to None (no change; board default 500 µs).
            ext_trig_lev (float, optional):
                External trigger level in Volts. SIGNALlab 250-12 only.
                Defaults to None (no change; board default 1 V).
            board (BoardModel, optional):
                Board model. Defaults to ``BoardModel.STEMLAB_125_14``.
        """
        self._validate_gen_trig_set_params(chan, trig_sour, ext_trig_deb_us, ext_trig_lev, board)

        if trig_sour is not None:
            self.tx_txt(f"SOUR{chan}:TRig:SOUR {trig_sour.value}")
        if ext_trig_deb_us is not None:
            self.tx_txt(f"SOUR:TRig:EXT:DEBouncer:US {ext_trig_deb_us}")
        if board == BoardModel.SIGNALLAB_250_12:
            if ext_trig_lev is not None:
                self.tx_txt(f"TRig:EXT:LEV {ext_trig_lev}")

        self.check_error()

    def gen_get_settings(
        self,
        chan: int,
        board: BoardModel = BoardModel.STEMLAB_125_14
    ) -> List[str]:
        """Retrieves waveform settings of one generator channel from Red Pitaya.

        Returns:
            List[str]: ``[func, volt, freq, offs, phas, dcyc, (load)]``.
            ``load`` is only present for SIGNALlab 250-12 and STEMlab Gen2 (index 6).

        Use :meth:`gen_get_trig_settings` to read back trigger settings.

        Args:
            chan (int): Output channel (either 1 or 2).
            board (BoardModel, optional): Board model. Defaults to ``BoardModel.STEMLAB_125_14``.
        """
        self._validate_channel(chan)

        settings = [
            self.txrx_txt(f"SOUR{chan}:FUNC?"),
            self.txrx_txt(f"SOUR{chan}:VOLT?"),
            self.txrx_txt(f"SOUR{chan}:FREQ:FIX?"),
            self.txrx_txt(f"SOUR{chan}:VOLT:OFFS?"),
            self.txrx_txt(f"SOUR{chan}:PHAS?"),
            self.txrx_txt(f"SOUR{chan}:DCYC?"),
        ]

        if board in (BoardModel.SIGNALLAB_250_12, BoardModel.STEMLAB_125_14_GEN2, BoardModel.STEMLAB_125_14_PRO_Z7020_GEN2):
            settings.append(self.txrx_txt(f"SOUR{chan}:LOAD?"))

        self.check_error()
        return settings

    def gen_get_trig_settings(
        self,
        chan: int,
        board: BoardModel = BoardModel.STEMLAB_125_14
    ) -> List[str]:
        """Retrieves trigger settings of one generator channel from Red Pitaya.

        Returns:
            List[str]: ``[trig_sour, ext_trig_deb_us, (ext_trig_lev)]``.
            ``ext_trig_lev`` is only present for SIGNALlab 250-12 (index 2).

        Use :meth:`gen_get_settings` to read back waveform settings.

        Args:
            chan (int): Output channel (either 1 or 2).
            board (BoardModel, optional): Board model. Defaults to ``BoardModel.STEMLAB_125_14``.
        """
        self._validate_channel(chan)

        settings = [
            self.txrx_txt(f"SOUR{chan}:TRig:SOUR?"),
            self.txrx_txt("SOUR:TRig:EXT:DEBouncer:US?"),
        ]

        if board == BoardModel.SIGNALLAB_250_12:
            settings.append(self.txrx_txt("TRig:EXT:LEV?"))

        self.check_error()
        return settings

    # Burst
    def gen_burst_mode(self, chan: int, enable: bool) -> None:
        """
        Enables or disables burst mode for the specified channel.

        Args:
            chan (int): Output channel (1 or 2).
            enable (bool): True to enable burst mode, False to return to continuous mode.
        """
        self._validate_channel(chan)
        self.tx_txt(f"SOUR{chan}:BURS:STAT {'BURST' if enable else 'CONTINUOUS'}")
        self.check_error()

    def gen_burst_set(
        self,
        chan: int,
        ncyc: int = 1,
        nor: int = 1,
        period: Optional[int] = None,
        init_val: float = 0,
        last_val: float = 0,
        board: BoardModel = BoardModel.STEMLAB_125_14
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
            board (BoardModel, optional):
                Board model. Defaults to ``BoardModel.STEMLAB_125_14``.
        """
        self._validate_burst_params(chan, ncyc, nor, period, init_val, last_val, board)

        self.tx_txt(f"SOUR{chan}:BURS:STAT BURST")
        self.tx_txt(f"SOUR{chan}:BURS:NCYC {ncyc}")
        self.tx_txt(f"SOUR{chan}:BURS:NOR {nor}")

        if period is not None:
            self.tx_txt(f"SOUR{chan}:BURS:INT:PER {period}")

        self.tx_txt(f"SOUR{chan}:BURS:LASTValue {last_val}")
        self.tx_txt(f"SOUR{chan}:BURS:INITValue {init_val}")

        self.check_error()

    def gen_get_burst_settings(self, chan: int) -> List[str]:
        """Retrieves burst generator settings of one channel from Red Pitaya.

        Returns:
            List[str]: ``[mode, ncyc, nor, period, init_val, last_val]``.

        Args:
            chan (int): Output channel (either 1 or 2).
        """
        settings = [
            self.txrx_txt(f"SOUR{chan}:BURS:STAT?"),
            self.txrx_txt(f"SOUR{chan}:BURS:NCYC?"),
            self.txrx_txt(f"SOUR{chan}:BURS:NOR?"),
            self.txrx_txt(f"SOUR{chan}:BURS:INT:PER?"),
            self.txrx_txt(f"SOUR{chan}:BURS:INITValue?"),
            self.txrx_txt(f"SOUR{chan}:BURS:LASTValue?")
        ]
        self.check_error()
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
        inf_rep: bool = False,
        rep_count: int = 1,
        board: BoardModel = BoardModel.STEMLAB_125_14
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
            mode (SweepMode, optional):
                Either linear (``SweepMode.LINEAR``) or logarithmic (``SweepMode.LOG``).
                Defaults to ``SweepMode.LINEAR``.
            direction (SweepDirection, optional):
                Sweep direction (``SweepDirection.NORMAL`` or ``SweepDirection.UP_DOWN``).
                Defaults to ``SweepDirection.NORMAL``.
            inf_rep (bool, optional):
                True if the sweep should be infinitely repeated. Defaults to False.
            rep_count (int, optional):
                Number of repetitions for the sweep when ``inf_rep`` is False. Defaults to 1.
            board (BoardModel, optional):
                Board model. Defaults to ``BoardModel.STEMLAB_125_14``.
        """

        self._validate_sweep_params(chan, start_freq, stop_freq, time_us, mode, direction, inf_rep, rep_count, board)

        self.tx_txt(f"SOUR{chan}:SWeep:STATE ON")
        self.tx_txt(f"SOUR{chan}:SWeep:FREQ:START {start_freq}")
        self.tx_txt(f"SOUR{chan}:SWeep:FREQ:STOP {stop_freq}")
        self.tx_txt(f"SOUR{chan}:SWeep:TIME {time_us}")
        self.tx_txt(f"SOUR{chan}:SWeep:MODE {mode.value}")
        self.tx_txt(f"SOUR{chan}:SWeep:DIR {direction.value}")

        if inf_rep:
            self.tx_txt(f"SOUR{chan}:SWeep:REP:INF ON")
        else:
            self.tx_txt(f"SOUR{chan}:SWeep:REP:INF OFF")
            self.tx_txt(f"SOUR{chan}:SWeep:REP:COUNT {rep_count}")

        self.check_error()

    def gen_get_sweep_settings(self, chan: int) -> List[str]:
        """Retrieves sweep mode settings of one channel from Red Pitaya.

        Returns:
            List[str]: ``[state, start_freq, stop_freq, time_us, mode, dir]``.

        Args:
            chan (int): Output channel (either 1 or 2).
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
        return settings

    def gen_sweep_state(self, chan: int, enable: bool) -> None:
        """
        Enables or disables sweep mode for the specified channel.

        Args:
            chan (int): Output channel (1 or 2).
            enable (bool): True to enable sweep mode, False to disable.
        """
        self._validate_channel(chan)
        self.tx_txt(f"SOUR{chan}:SWeep:STATE {'ON' if enable else 'OFF'}")
        self.check_error()

    def gen_sweep_pause(self, chan: int, pause: bool) -> None:
        """
        Pauses or resumes sweep mode for the specified channel.

        Args:
            chan (int): Output channel (1 or 2).
            pause (bool): True to pause, False to resume.
        """
        self._validate_channel(chan)
        self.tx_txt(f"SOUR{chan}:SWeep:PAUSE {'ON' if pause else 'OFF'}")
        self.check_error()


    # Validations
    def _validate_gen_set_params(
        self,
        chan: int,
        func: Waveform,
        ampl: float,
        freq: float,
        offset: Optional[float],
        phase: Optional[float],
        dcyc: Optional[float],
        data: Optional[np.ndarray],
        load: Optional[GenLoad],
        board: BoardModel
    ) -> None:
        """
        Validate parameters for gen_set function.
        """
        buff_size = 16384

        volt_lim = 5 if board == BoardModel.SIGNALLAB_250_12 else 1
        phase_lim = 360
        freq_up_lim = 60e6 if board == BoardModel.SDRLAB_122_16 else 50e6
        freq_down_lim = 300e3 if board == BoardModel.SDRLAB_122_16 else 0

        if chan not in (1, 2):
            raise ValueError("Channel needs to be either 1 or 2.")
        if not (freq_down_lim <= freq <= freq_up_lim):
            raise ValueError(f"Frequency {freq} Hz is out of range [{freq_down_lim}, {freq_up_lim}] Hz.")
        if abs(ampl) > volt_lim:
            raise ValueError(f"Amplitude {ampl} V is out of range [{-volt_lim}, {volt_lim}] V.")
        if offset is not None:
            if abs(offset) > volt_lim:
                raise ValueError(f"Offset {offset} V is out of range [{-volt_lim}, {volt_lim}] V.")
        if dcyc is not None:
            if not (0 <= dcyc <= 1):
                raise ValueError("Duty Cycle is out of range [0, 1].")
        if phase is not None:
            if abs(phase) > phase_lim:
                raise ValueError(f"Phase {phase} deg is out of range [{-phase_lim}, {phase_lim}] deg.")
        if data is not None:
            if data.shape[0] > buff_size:
                raise ValueError(f"Data array is too long. Max length is {buff_size}.")
        if load is not None:
            _LOAD_BOARDS = (
                BoardModel.SIGNALLAB_250_12,
                BoardModel.STEMLAB_125_14_GEN2,
                BoardModel.STEMLAB_125_14_PRO_Z7020_GEN2,
                BoardModel.STEMLAB_125_14_TI,
                BoardModel.STEMLAB_65_16_TI,
            )
            if board not in _LOAD_BOARDS:
                raise ValueError(
                    "Load setting is only available on SIGNALlab 250-12, "
                    "STEMlab 125-14 Gen2, STEMlab 125-14 Pro Z7020 Gen2, STEMlab 125-14 TI, and STEMlab 65-16 TI."
                )

    def _validate_gen_trig_set_params(
        self,
        chan: int,
        trig_sour: Optional[TriggerSource],
        ext_trig_deb_us: Optional[int],
        ext_trig_lev: Optional[float],
        board: BoardModel
    ) -> None:
        """
        Validate parameters for gen_trig_set function.
        """
        volt_lim = 5 if board == BoardModel.SIGNALLAB_250_12 else 1

        if chan not in (1, 2):
            raise ValueError("Channel needs to be either 1 or 2.")
        if ext_trig_deb_us is not None:
            if ext_trig_deb_us < 1:
                raise ValueError(
                    f"External trigger debounce filter value {ext_trig_deb_us} is out of range. The minimal value is 1 microsecond."
                )
        if ext_trig_lev is not None:
            if board != BoardModel.SIGNALLAB_250_12:
                raise ValueError("External trigger level setting is only available on SIGNALlab 250-12.")
            if abs(ext_trig_lev) > volt_lim:
                raise ValueError(f"External trigger level {ext_trig_lev} V is out of range [{-volt_lim}, {volt_lim}] V.")

    def _validate_burst_params(
        self,
        chan: int,
        ncyc: int,
        nor: int,
        period: Optional[int],
        init_val: float,
        last_val: float,
        board: BoardModel
    ) -> None:
        """
        Validate parameters for gen_burst_set function.
        """
        volt_lim = 5.0 if board == BoardModel.SIGNALLAB_250_12 else 1.0

        self._validate_channel(chan)
        if ncyc < 1:
            raise ValueError("NCYC minimum is 1.")
        if nor < 1:
            raise ValueError("NOR minimum is 1.")
        if period is not None:
            if period < 1:
                raise ValueError("Minimal burst period is 1 µs.")
        if abs(last_val) > volt_lim:
            raise ValueError(f"Last value {last_val} V is out of range [{-volt_lim}, {volt_lim}] V.")
        if abs(init_val) > volt_lim:
            raise ValueError(f"Init value {init_val} V is out of range [{-volt_lim}, {volt_lim}] V.")

    def _validate_sweep_params(
        self,
        chan: int,
        start_freq: int,
        stop_freq: int,
        time_us: int,
        mode: SweepMode,
        direction: SweepDirection,
        inf_rep: bool,
        rep_count: int,
        board: BoardModel
    ) -> None:
        """
        Validate parameters for gen_sweep_set function.
        """
        freq_up_lim = 60e6 if board == BoardModel.SDRLAB_122_16 else 50e6
        freq_down_lim = 300e3 if board == BoardModel.SDRLAB_122_16 else 0

        self._validate_channel(chan)
        if not (freq_down_lim <= start_freq <= freq_up_lim):
            raise ValueError(f"Start frequency {start_freq} Hz is out of range [{freq_down_lim}, {freq_up_lim}] Hz.")
        if not (freq_down_lim <= stop_freq <= freq_up_lim):
            raise ValueError(f"Stop frequency {stop_freq} Hz is out of range [{freq_down_lim}, {freq_up_lim}] Hz.")
        if start_freq >= stop_freq:
            raise ValueError("Start frequency must be lower than Stop frequency.")
        if time_us < 1:
            raise ValueError("Minimal sweep period is 1 µs.")
        if not isinstance(inf_rep, bool):
            raise ValueError("inf_rep must be a boolean.")
        if rep_count < 1:
            raise ValueError("Repetition count must be at least 1.")

    def _validate_channel(self, chan: int) -> None:
        """
        Validate the channel number.
        """
        if chan not in (1, 2):
            raise ValueError("Channel needs to be either 1 or 2.")



    ### ACQUISITION ###

    def acq_set(
        self,
        dec: int = 1,
        units: Optional[Units] = None,
        data_format: Optional[DataFormat] = None,
        byte_order: Optional[ByteOrder] = None,
        averaging: bool = True,
        gain: Optional[List[Gain]] = None,
        coupling: Optional[List[Coupling]] = None,
        board: BoardModel = BoardModel.STEMLAB_125_14
    ) -> None:

        """
        Set the parameters for the standard signal acquisition.

        Args:
            dec (int, optional):
                Decimation factor (1, 2, 4, 8, 16, 17, ..., 65536).
                Defaults to 1.
            units (Units, optional):
                Units for the acquired data (``Units.VOLTS`` or ``Units.RAW``).
                Defaults to None (VOLTS).
            data_format (DataFormat, optional):
                Format for the acquired data (``DataFormat.ASCII`` or ``DataFormat.BIN``).
                Defaults to None (ASCII).
            byte_order (ByteOrder, optional):
                Byte order for binary data (``ByteOrder.BEND`` or ``ByteOrder.LEND``).
                Defaults to None (BEND).
            averaging (bool, optional):
                When True, each returned sample is the average of the decimated samples.
                Defaults to True.
            gain (List[Gain], optional):
                HV/LV gain per channel. Length 2 (or 4 for STEMlab 4-Input).
                Not applicable to SDRlab 122-16. Defaults to None.
            coupling (List[Coupling], optional):
                AC/DC coupling per channel. SIGNALlab 250-12 only. Defaults to None.
            board (BoardModel, optional):
                Board model. Defaults to ``BoardModel.STEMLAB_125_14``.
        """
        self._validate_acq_set_params(dec, units, data_format, gain, coupling, board)

        n = 4 if board == BoardModel.STEMLAB_125_14_4INPUT else 2

        self.tx_txt(f"ACQ:DEC:Factor {dec}")
        self.tx_txt(f"ACQ:AVG {'ON' if averaging else 'OFF'}")
        if units is not None:
            self.tx_txt(f"ACQ:DATA:Units {units.value}")
        if data_format is not None:
            self.tx_txt(f"ACQ:DATA:FORMAT {data_format.value}")
        if byte_order is not None:
            self.tx_txt(f"ACQ:DATA:BYTE:ORDER {byte_order.value}")

        if gain is not None and board != BoardModel.SDRLAB_122_16:
            for i, g in enumerate(gain[:n], start=1):
                self.tx_txt(f"ACQ:SOUR{i}:GAIN {g.value}")
        if coupling is not None and board == BoardModel.SIGNALLAB_250_12:
            for i, c in enumerate(coupling[:n], start=1):
                self.tx_txt(f"ACQ:SOUR{i}:COUP {c.value}")

        self.check_error()

    def acq_get_settings(self, board: BoardModel = BoardModel.STEMLAB_125_14) -> List[str]:
        """Retrieves standard acquisition settings from Red Pitaya.

        Returns:
            List[str]: ``[dec_factor, average, units, data_format, buf_size,
            gain_ch1, gain_ch2, (gain_ch3, gain_ch4,) (coup_ch1, coup_ch2)]``.

        Args:
            board (BoardModel, optional): Board model. Defaults to ``BoardModel.STEMLAB_125_14``.
        """
        n = 4 if board == BoardModel.STEMLAB_125_14_4INPUT else 2

        settings = [
            self.txrx_txt("ACQ:DEC:Factor?"),
            self.txrx_txt("ACQ:AVG?"),
            self.txrx_txt("ACQ:DATA:Units?"),
            self.txrx_txt("ACQ:DATA:FORMAT?"),
            self.txrx_txt("ACQ:BUF:SIZE?")
        ]

        if board != BoardModel.SDRLAB_122_16:
            for i in range(n):
                settings.append(self.txrx_txt(f"ACQ:SOUR{i+1}:GAIN?"))

        if board == BoardModel.SIGNALLAB_250_12:
            for i in range(2):
                settings.append(self.txrx_txt(f"ACQ:SOUR{i+1}:COUP?"))
        self.check_error()

        return settings

    def acq_start(self) -> None:
        """
        Starts the acquisition.
        """
        self.tx_txt("ACQ:START")
        self.check_error()

    def acq_arm(self, source: AcqTrigSource) -> None:
        """
        Arms the acquisition by setting the trigger source.
        Must be called after acq_start().

        Parameters
        ----------
            source (AcqTrigSource) :
                Trigger source. Use AcqTrigSource.DISABLED for an
                immediate (untriggered) acquisition.
        """
        self.tx_txt(f"ACQ:TRig {source.value}")
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
        board: BoardModel = BoardModel.STEMLAB_125_14
    ) -> None:
        """
        Set the trigger parameters for the standard signal acquisition.
        One trigger is used for all acquisition channels.

        Args:
            trig_lvl (float, optional):
                Trigger level in Volts. {-1, 1} V on LV gain or {-20, 20} V on HV gain.
                Defaults to 0.
            trig_delay (int, optional):
                Trigger delay in samples (or in ns if ``trig_delay_ns`` is True).
                Defaults to 0.
            trig_delay_ns (bool, optional):
                When True, ``trig_delay`` is interpreted as nanoseconds.
                Defaults to False.
            trig_hyst (float, optional):
                Trigger hysteresis threshold in Volts. Defaults to None.
            ext_trig_deb_us (int, optional):
                External trigger debounce filter length in microseconds.
                Defaults to None.
            ext_trig_lvl (float, optional):
                External trigger level in Volts. SIGNALlab 250-12 only.
                Defaults to None.
            board (BoardModel, optional):
                Board model. Defaults to ``BoardModel.STEMLAB_125_14``.
        """
        n = 4 if board == BoardModel.STEMLAB_125_14_4INPUT else 2
        gains = [self.txrx_txt(f"ACQ:SOUR{i+1}:GAIN?").upper() for i in range(n)]
        self._validate_acq_trig_params(trig_lvl, trig_delay, trig_hyst, ext_trig_deb_us, ext_trig_lvl, board, gains)

        if trig_delay_ns:
            self.tx_txt(f"ACQ:TRig:DLY:NS {trig_delay}")
        else:
            self.tx_txt(f"ACQ:TRig:DLY {trig_delay}")

        if trig_hyst is not None:
            self.tx_txt(f"ACQ:TRig:HYST {trig_hyst}")

        if ext_trig_deb_us is not None:
            self.tx_txt(f"ACQ:TRig:EXT:DEBouncer:US {ext_trig_deb_us}")

        self.tx_txt(f"ACQ:TRig:LEV {trig_lvl}")

        if board == BoardModel.SIGNALLAB_250_12 and ext_trig_lvl is not None:
            self.tx_txt(f"TRig:EXT:LEV {ext_trig_lvl}")

        self.check_error()

    def acq_get_trig_settings(self, board: BoardModel = BoardModel.STEMLAB_125_14) -> List[str]:
        """Retrieves standard acquisition trigger settings from Red Pitaya.

        Returns:
            List[str]: ``[trig_dly, trig_dly_ns, trig_lvl, trig_hyst,
            ext_trig_deb_us, (ext_trig_lvl)]``.
            ``ext_trig_lvl`` is only present for SIGNALlab 250-12 (index 5).

        Args:
            board (BoardModel, optional): Board model. Defaults to ``BoardModel.STEMLAB_125_14``.
        """
        settings = [
            self.txrx_txt("ACQ:TRig:DLY?"),
            self.txrx_txt("ACQ:TRig:DLY:NS?"),
            self.txrx_txt("ACQ:TRig:LEV?"),
            self.txrx_txt("ACQ:TRig:HYST?"),
            self.txrx_txt("ACQ:TRig:EXT:DEBouncer:US?")
        ]

        if board == BoardModel.SIGNALLAB_250_12:
            settings.append(self.txrx_txt("TRig:EXT:LEV?"))

        self.check_error()
        return settings

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

    def acq_data_byte_order_set(self, byte_order: Union[ByteOrder, str]) -> None:
        """
        Set the byte order for binary data acquisition.

        Args:
            byte_order: ByteOrder enum (ByteOrder.LEND / ByteOrder.BEND) or
                        plain string ('LEND' / 'BEND').
        """
        if isinstance(byte_order, ByteOrder):
            value = byte_order.value
        else:
            value = byte_order
        if value not in ('LEND', 'BEND'):
            raise ValueError("byte_order must be 'LEND' or 'BEND'")
        self.tx_txt(f"ACQ:DATA:BYTE:ORDER {value}")
        self.check_error()

    def acq_data_byte_order_get(self) -> str:
        """
        Get the current byte order for binary data acquisition.
        
        Returns:
            'LEND' for little-endian or 'BEND' for big-endian
        """
        return self.txrx_txt("ACQ:DATA:BYTE:ORDER?")

    # Split trigger mode
    def acq_split_mode(self, enable: bool) -> None:
        """
        Enables or disables acquisition split trigger mode.

        Args:
            enable (bool): True to enable split trigger mode, False to disable.
        """
        self.tx_txt(f"ACQ:SPLIT:TRig {'ON' if enable else 'OFF'}")
        self.check_error()

    #TODO add get settings
    def acq_split_set(
        self,
        chan: int,
        dec: int = 1,
        averaging: bool = True,
        gain: Optional[Gain] = None,
        coupling: Optional[Coupling] = None,
        board: BoardModel = BoardModel.STEMLAB_125_14
    ) -> None:

        """
        Set the parameters for a specific acquisition channel using the split trigger
        signal acquisition mode. Each channel has its own trigger.

        Args:
            chan (int):
                Input acquisition channel (1 or 2; 1–4 for STEMlab 125-14 4-Input).
            dec (int, optional):
                Decimation factor (1, 2, 4, 8, 16, 17, ..., 65536). Defaults to 1.
            averaging (bool, optional):
                When True, each returned sample is the average of the decimated samples.
                Defaults to True.
            gain (Gain, optional):
                HV/LV gain for this channel. Not applicable to SDRlab 122-16.
                Defaults to None.
            coupling (Coupling, optional):
                AC/DC coupling mode. SIGNALlab 250-12 only. Defaults to None.
            board (BoardModel, optional):
                Board model. Defaults to ``BoardModel.STEMLAB_125_14``.
        """
        self._validate_acq_split_params(chan, dec, gain, coupling, board)

        self.tx_txt(f"ACQ:DEC:Factor:CH{chan} {dec}")
        self.tx_txt(f"ACQ:AVG:CH{chan} {'ON' if averaging else 'OFF'}")
        if gain is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:GAIN {gain.value}")
        if board == BoardModel.SIGNALLAB_250_12 and coupling is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:COUP {coupling.value}")

        self.check_error()

    def acq_split_trig_set(
        self,
        chan: int,
        trig_lvl: float = 0,
        trig_delay: int = 0,
        trig_delay_ns: bool = False,
        board: BoardModel = BoardModel.STEMLAB_125_14
    ) -> None:
        """
        Set the trigger parameters for the split trigger acquisition.
        Each channel uses a separate trigger.

        Args:
            chan (int):
                Input acquisition channel (1 or 2; 1–4 for STEMlab 125-14 4-Input).
            trig_lvl (float, optional):
                Trigger level in Volts. {-1, 1} V on LV gain or {-20, 20} V on HV gain.
                Defaults to 0.
            trig_delay (int, optional):
                Trigger delay in samples (or ns if ``trig_delay_ns`` is True).
                Defaults to 0.
            trig_delay_ns (bool, optional):
                When True, ``trig_delay`` is interpreted as nanoseconds.
                Defaults to False.
            board (BoardModel, optional):
                Board model. Defaults to ``BoardModel.STEMLAB_125_14``.
        """
        gain = self.txrx_txt(f"ACQ:SOUR{chan}:GAIN?").upper()
        self._validate_acq_split_trig_params(chan, trig_lvl, trig_delay, board, gain)

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
        latest: bool = False,
        trig_pos: Optional[DataTriggerPosition] = None,
        data_format: Optional[DataFormat] = None,
        data_units: Optional[Units] = None,
        byte_order: Optional[ByteOrder] = None,
        board: BoardModel = BoardModel.STEMLAB_125_14,
    ) -> np.ndarray:
        """
        Returns the acquired data on a channel from the Red Pitaya, with the following options (for a specific channel):
            - only channel       => returns the whole buffer
            - start and end      => returns the samples between them
            - start and n        => returns 'n' samples from the start position
            - old and n          => returns 'n' oldest samples in the buffer
            - lat and n          => returns 'n' latest samples in the buffer
            - trig_pos and n     => returns 'n' samples around trigger position (depends on setting)

        When *data_format*, *data_units*, and *byte_order* are supplied (matching
        what was passed to :meth:`acq_set`), no extra SCPI queries are issued per
        call. If any parameter is ``None`` its value is queried from the board.

        Args:
            chan (int):
                Input acquisition channel (1 or 2; 1–4 for STEMlab 125-14 4-Input).
            start (int, optional):
                Start position in the buffer {0, ..., 16384}. Defaults to None.
            end (int, optional):
                End position in the buffer {0, ..., 16384}. Defaults to None.
            num_samples (int, optional):
                Number of samples to read. Defaults to None.
            old (bool, optional):
                Read oldest samples in the buffer. Defaults to False.
            latest (bool, optional):
                Read latest samples in the buffer. Defaults to False.
            trig_pos (DataTriggerPosition, optional):
                Read samples around trigger position (PRE_TRIG, POST_TRIG, PRE_POST_TRIG).
                Defaults to None.
            data_format (DataFormat, optional):
                Expected data format. Defaults to None (queried from board).
            data_units (Units, optional):
                Expected data units. Defaults to None (queried from board).
            byte_order (ByteOrder, optional):
                Byte order for binary data. Defaults to None (queried from board).
            board (BoardModel, optional):
                Board model. Defaults to ``BoardModel.STEMLAB_125_14``.

        Returns:
            np.ndarray: Numpy array with captured data.
        """
        self._validate_acq_data_params(chan, start, end, num_samples, old, latest, trig_pos, board)

        units_str  = data_units.value   if data_units   is not None else self.txrx_txt('ACQ:DATA:Units?')
        format_str = data_format.value  if data_format  is not None else self.txrx_txt("ACQ:DATA:FORMAT?")

        # Determine the output data
        if start is not None and end is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:DATA:STArt:End? {start},{end}")
        elif start is not None and num_samples is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:DATA:STArt:N? {start},{num_samples}")
        elif old and num_samples is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:DATA:Old:N? {num_samples}")
        elif latest and num_samples is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:DATA:LATest:N? {num_samples}")
        elif trig_pos is not None and num_samples is not None:
            self.tx_txt(f"ACQ:SOUR{chan}:DATA:TRig? {num_samples},{trig_pos.value}")
        else:
            self.tx_txt(f"ACQ:SOUR{chan}:DATA?")

        # Convert data
        if format_str == "BIN":
            buff_byte = self.rx_arb()
            if not isinstance(buff_byte, bytes):
                raise ValueError("Failed to receive binary data")

            if byte_order is not None:
                order_str = byte_order.value
            else:
                try:
                    order_str = self.txrx_txt('ACQ:DATA:BYTE:ORDER?').strip()
                except Exception:
                    order_str = ByteOrder.LEND.value    # little-endian fallback

            if order_str == ByteOrder.LEND.value:
                float_dtype, int_dtype = '<f4', '<i2'
            else:
                float_dtype, int_dtype = '>f4', '>i2'

            if units_str == Units.VOLTS.value:
                buff = np.frombuffer(buff_byte, dtype=float_dtype)
            elif units_str == Units.RAW.value:
                buff = np.frombuffer(buff_byte, dtype=int_dtype)
            else:
                raise ValueError(f"Unsupported units: {units_str}")

            buff = buff.astype(np.float64)
        else:
            buff_string = self.rx_txt().strip('{}\n\r').replace("  ", "").split(',')
            buff = np.array(buff_string, dtype=np.float64)
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
        board: BoardModel
    ) -> None:
        """
        Validate parameters for acq_set function.
        """
        dec_fact_list = [1, 2, 4, 8]

        if not ((dec in dec_fact_list) or (16 <= dec <= 65536)):
            raise ValueError("Decimation factor out of range [1,2,4,8,16,17,18,...,65536].")
        if gain is not None and board == BoardModel.SDRLAB_122_16:
            raise ValueError("Gain setting is not available for SDRlab 122-16 (no gain jumpers)")
        if coupling is not None and board != BoardModel.SIGNALLAB_250_12:
            raise ValueError("Coupling setting is only available for SIGNALlab 250-12")

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
            if units.value not in units_list:
                raise ValueError(f"{units.value} is not a defined unit.")
        if data_format is not None:
            if data_format.value not in format_list:
                raise ValueError(f"{data_format.value} is not a defined format.")

    def _validate_acq_trig_params(
        self,
        trig_lvl: float,
        trig_delay: int,
        trig_hyst: Optional[float],
        ext_trig_deb_us: Optional[int],
        ext_trig_lvl: Optional[float],
        board: BoardModel,
        gains: List[str]
    ) -> None:
        """
        Validate parameters for acq_trig_set function.
        """
        trig_lvl_lim = 20.0 if any(g == "HV" for g in gains) else 1.0
        ext_trig_lvl_limit = 5.0

        if abs(trig_lvl) > trig_lvl_lim:
            raise ValueError(f"Trigger level out of range [{-trig_lvl_lim}, {trig_lvl_lim}] V.")
        if trig_delay < 0:
            raise ValueError("Trigger delay cannot be less than 0.")
        if trig_hyst is not None:
            if trig_hyst < 0:
                raise ValueError("Trigger hysteresis cannot be negative.")
        if board == BoardModel.SIGNALLAB_250_12 and ext_trig_lvl is not None:
            if abs(ext_trig_lvl) > ext_trig_lvl_limit:
                raise ValueError(f"External trigger level out of range [{-ext_trig_lvl_limit}, {ext_trig_lvl_limit}] V.")
        if ext_trig_deb_us is not None:
            if ext_trig_deb_us < 1:
                raise ValueError("External trigger debounce filter value is out of range. The minimal value is 1 microsecond.")

    def _validate_acq_split_params(
        self,
        chan: int,
        dec: int,
        gain: Optional[Gain],
        coupling: Optional[Coupling],
        board: BoardModel
    ) -> None:
        """
        Validate parameters for acq_split_set function.
        """
        dec_fact_list = [1, 2, 4, 8]

        n = 4 if board == BoardModel.STEMLAB_125_14_4INPUT else 2

        if not (1 <= chan <= n):
            raise ValueError(f"Channel {chan} out of range [1, {n}].")
        if not ((dec in dec_fact_list) or (16 <= dec <= 65536)):
            raise ValueError("Decimation factor out of range [1,2,4,8,16,17,18,...,65536].")
        if gain is not None and board == BoardModel.SDRLAB_122_16:
            raise ValueError("Gain setting is not available for SDRlab 122-16 (no gain jumpers)")
        if coupling is not None and board != BoardModel.SIGNALLAB_250_12:
            raise ValueError("Coupling setting is only available for SIGNALlab 250-12")

    def _validate_acq_split_trig_params(
        self,
        chan: int,
        trig_lvl: float,
        trig_delay: int,
        board: BoardModel,
        gain: str
    ) -> None:
        """
        Validate parameters for acq_split_trig_set function.
        """
        n = 4 if board == BoardModel.STEMLAB_125_14_4INPUT else 2
        trig_lvl_lim = 20.0 if gain == "HV" else 1.0

        if not (1 <= chan <= n):
            raise ValueError(f"Channel {chan} out of range [1, {n}].")
        if abs(trig_lvl) > trig_lvl_lim:
            raise ValueError(f"Trigger level out of range [{-trig_lvl_lim}, {trig_lvl_lim}] V for gain {gain}.")
        if trig_delay < 0:
            raise ValueError("Trigger delay cannot be less than 0.")

    def _validate_acq_data_params(
        self,
        chan: int,
        start: Optional[int],
        end: Optional[int],
        num_samples: Optional[int],
        old: bool,
        latest: bool,
        trig_pos: Optional[DataTriggerPosition],
        board: BoardModel
    ) -> None:
        """
        Validate parameters for acq_data function.
        """
        n = 4 if board == BoardModel.STEMLAB_125_14_4INPUT else 2
        low_lim = 0
        up_lim = 16384

        if not (1 <= chan <= n):
            raise ValueError(f"Channel {chan} out of range [1, {n}].")
        if old and latest:
            raise ValueError("'old' and 'latest' cannot both be True.")
        if start is not None:
            if not (low_lim <= start <= up_lim):
                raise ValueError(f"Start position out of range [{low_lim}, {up_lim}].")
        if end is not None:
            if not (low_lim <= end <= up_lim):
                raise ValueError(f"End position out of range [{low_lim}, {up_lim}].")
        if num_samples is not None:
            if not (low_lim <= num_samples <= up_lim):
                raise ValueError(f"Sample number out of range [{low_lim}, {up_lim}].")
            if trig_pos is not None:
                if trig_pos not in DataTriggerPosition:
                    raise ValueError(f"Trigger position value {trig_pos} is not defined.")
                if trig_pos == DataTriggerPosition.PRE_POST_TRIG:
                    if num_samples * 2 + 1 > up_lim:
                        raise ValueError(f"Sample number is too big for {trig_pos.value} setting. This mode returns num_samples*2+1 data samples.")

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
        self.tx_txt("UART:SETUP")
        self.check_error()

    def uart_get_settings(self) -> List[str]:
        """Retrieves UART settings from Red Pitaya.

        Returns:
            List[str]: ``[speed, databits, stopbits, parity, timeout]``.
        """
        settings = [
            self.txrx_txt("UART:SPEED?"),
            self.txrx_txt("UART:BITS?"),
            self.txrx_txt("UART:STOPB?"),
            self.txrx_txt("UART:PARITY?"),
            self.txrx_txt("UART:TIMEOUT?")
        ]
        return settings

    #TODO add BIN, OCT, DEC, HEX data option
    def uart_write_string(
        self,
        string: str,
        use_ascii: bool = True
    ) -> None:
        """
        Sends a string of characters through UART.

        Args:
            string (str): The string to send.
            use_ascii (bool, optional): When True, encode using ASCII; when False, use UTF-8.
                Defaults to True (ASCII).
        """
        code = "ascii" if use_ascii else "utf-8"
        arr = ',#H'.join(format(x, 'X') for x in bytearray(string, code))
        self.tx_txt(f"UART:WRITE{len(string)} #H{arr}")

    def uart_read_string(
        self,
        length: int
    ) -> str:
        """
        Reads a string of data from UART and decodes it from ASCII to string.
        """
        if length <= 0:
            raise ValueError("Length must be greater than 0.")
        #TODO decode into UTF8 or ASCII

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
        speed_list = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400, 576000, 921600, 1000000, 1152000, 1500000, 2000000, 2500000, 3000000, 3500000, 4000000]
        bits_list = [e.value for e in UartBits]
        parity_list = [e.value for e in UartParity]

        if speed not in speed_list:
            raise ValueError(f"{speed} is not a defined speed for UART connection. Please check the speed table.")
        if bits.value not in bits_list:
            raise ValueError(f"{bits.value} is not a defined character size.")
        if parity.value not in parity_list:
            raise ValueError(f"{parity.value} is not a defined parity.")
        if stop not in (1, 2):
            raise ValueError("The number of stop bits can only be 1 or 2.")
        if not (0 <= timeout <= 255):
            raise ValueError(f"Timeout {timeout} is out of range [0, 255].")

    ### SPI ###

    def spi_init(
        self
    ) -> None:
        """
        Initializes the SPI interface.
        """
        self.tx_txt('SPI:INIT:DEV "/dev/spidev2.0"')    # OS versions IN DEV and higher
        #self.tx_txt('SPI:INIT:DEV "/dev/spidev1.0"')   # OS versions 2.05-37 and lower
        self.check_error()
    
    def spi_set(
        self,
        spi_mode: SPIMode = SPIMode.LISL,
        cs_mode: SPICSMode = SPICSMode.NORMAL,
        speed: int = 50000000,
        word_len: int = 8
    ) -> None:
        """
        Configures the provided settings for SPI.

        Args:
            spi_mode (SPIMode, optional): Sets the mode for SPI; - LISL (Low Idle level, Sample Leading edge)
                                                            - LIST (Low Idle level, Sample Trailing edge)
                                                            - HISL (High Idle level, Sample Leading edge)
                                                            - HIST (High Idle level, Sample Trailing edge)
                                                        Defaults to LISL.
            cs_mode (SPICSMode, optional): Sets the mode for CS: - NORMAL (After message transmission, CS => HIGH)
                                                            - HIGH (After message transmission, CS => LOW)
                                                        Defaults to NORMAL.
            speed (int, optional): Sets the speed of the SPI connection. Defaults to 50000000.
            word_len (int, optional): Character size in bits (6, 7, 8). Defaults to 8.
        """
        self._validate_spi_params(spi_mode, cs_mode, speed, word_len)

        # Configuring SPI

        self.tx_txt(f"SPI:SETtings:MODE {spi_mode.value}")
        self.tx_txt(f"SPI:SETtings:CSMODE {cs_mode.value}")
        self.tx_txt(f"SPI:SETtings:SPEED {speed}")
        self.tx_txt(f"SPI:SETtings:WORD {word_len}")

        self.tx_txt("SPI:SETtings:SET")
        self.check_error()

    def spi_get_settings(
        self
    ) -> List[str]:
        """Retrieves SPI settings from Red Pitaya.

        Returns:
            List[str]: ``[mode, csmode, speed, word_len, msg_size]``.
        """
        self.tx_txt("SPI:SETtings:GET")
        settings = [
            self.txrx_txt("SPI:SETtings:MODE?"),
            self.txrx_txt("SPI:SETtings:CSMODE?"),
            self.txrx_txt("SPI:SETtings:SPEED?"),
            self.txrx_txt("SPI:SETtings:WORD?"),
            self.txrx_txt("SPI:MSG:SIZE?")
        ]
        return settings

    def spi_create_msg(
        self,
        msg_num: int = 1
    ) -> int:
        """
        Creates new messages in the message queue.
        Returns the legth of the message queue.
        """
        self.tx_txt(f"SPI:MSG:CREATE {msg_num}")
        queue_len = self.txrx_txt("SPI:MSG:SIZE?")
        if queue_len is None:
            raise RuntimeError("SPI message queue creation failed: no response from board.")
        self.check_error()
        return int(queue_len)

    #TODO add BIN, OCT, DEC, HEX data option
    #TODO not really write, read, writeread as this just configures the messages
    def spi_conf_tx(
        self,
        data: str,
        msg_num: int = 0,
        cs_change: bool = False
    )-> None:
        """Configure the specified SPI message. Only set the transmit buffer!

        Parameters
        ----------
        data : str
            String of data to be sent.
        msg_num : int, optional
            Message number to save the data to, by default 0
        cs_change : bool, optional
            Change the state of the CS line after the message is sent, by default False
        """
        if len(data) == 0:
            raise ValueError("Data must not be empty.")
        if msg_num < 0:
            raise ValueError("Message number must not be negative.")
        if cs_change:
            self.tx_txt(f"SPI:MSG{msg_num}:TX{len(data)}:CS {','.join(str(ord(char)) for char in data)}")
        else:
            self.tx_txt(f"SPI:MSG{msg_num}:TX{len(data)} {','.join(str(ord(char)) for char in data)}")
        self.check_error()
    
    def spi_conf_rx(
        self,
        data_len: int,
        msg_num: int = 0,
        cs_change: bool = False
    ) -> None:
        """Initialize the SPI receive buffer for specific message. Only set the receive buffer!

        Parameters
        ----------
        data_len : int
            Length of data to be read.
        msg_num : int, optional
            Message number to read data from, by default 0
        cs_change : bool, optional
            Change the state of the CS line after the message is sent, by default False
        """
        
        if data_len <= 0:
            raise ValueError("Data length must be greater than 0.")
        if msg_num < 0:
            raise ValueError("Message number must not be negative.")
        if cs_change:
            self.tx_txt(f"SPI:MSG{msg_num}:RX{data_len}:CS")
        else:
            self.tx_txt(f"SPI:MSG{msg_num}:RX{data_len}")
        self.check_error()
    
    def spi_conf_txrx(
        self,
        data: str,
        msg_num: int = 0,
        cs_change: bool = False
    ) -> None:
        """Configure the specified SPI message and initialize the corresponding receive buffer.

        Parameters
        ----------
        data : str
            String of data to be sent.
        msg_num : int, optional
            Message number to save the data to, by default 0
        cs_change : bool, optional
            Change the state of the CS line after the message is sent, by default False
        """
        if len(data) == 0:
            raise ValueError("Data must not be empty.")
        if msg_num < 0:
            raise ValueError("Message number must not be negative.")
        if cs_change:
            self.tx_txt(f"SPI:MSG{msg_num}:TX{len(data)}:RX:CS {','.join(str(ord(char)) for char in data)}")
        else:
            self.tx_txt(f"SPI:MSG{msg_num}:TX{len(data)}:RX {','.join(str(ord(char)) for char in data)}")
        self.check_error()
    
    def spi_get_tx_buff(
        self,
        msg_num: int = 0
    ) -> str:
        """Get the data from the transmit buffer.

        Parameters
        ----------
        msg_num : int, optional
            Message number to get the data from, by default 0
        """
        if msg_num < 0:
            raise ValueError("Message number must not be negative.")
        tx_buff = self.txrx_txt(f"SPI:MSG{msg_num}:TX?")
        if tx_buff is None:
            raise RuntimeError(f"SPI TX buffer read failed for message {msg_num}: no response from board.")
        tx_buff = tx_buff.strip('{}\n\r').replace("  ", "")
        self.check_error()
        return ''.join(chr(int(x)) for x in tx_buff.split(','))
    
    def spi_get_rx_buff(
        self,
        msg_num: int = 0
    ) -> str:
        """Get the data from the receive buffer.

        Parameters
        ----------
        msg_num : int, optional
            Message number to get the data from, by default 0
        """
        if msg_num < 0:
            raise ValueError("Message number must not be negative.")
        rx_buff = self.txrx_txt(f"SPI:MSG{msg_num}:RX?")
        if rx_buff is None:
            raise RuntimeError(f"SPI RX buffer read failed for message {msg_num}: no response from board.")
        rx_buff = rx_buff.strip('{}\n\r').replace("  ", "")
        self.check_error()
        return ''.join(chr(int(x)) for x in rx_buff.split(','))
    
    def spi_write_read(
        self,
        data: str,
        msg_num: int = 0
    ) -> str:
        """Write the data to the SPI transmit buffer, start the transmission and read the data from the receive buffer.
        This function is used for a single message only.
        
        Parameters
        ----------
        data : str
            String of data to be sent.
        msg_num : int, optional
            Message number to save the data to, by default 0
        
        Returns
        -------
        str
            Received data in string format.
        """
        if len(data) == 0:
            raise ValueError("Data must not be empty.")
        queue_len = self.txrx_txt("SPI:MSG:SIZE?")
        if queue_len is None:
            raise RuntimeError("SPI message queue error: no response from board.")
        if not (0 <= msg_num < int(queue_len)):
            raise ValueError(f"Message number {msg_num} out of range [0, {int(queue_len)}).")
        self.spi_conf_txrx(data, msg_num, False)
        self.tx_txt("SPI:PASS")
        rx_data = self.spi_get_rx_buff(msg_num)

        return rx_data

    # Validate
    def _validate_spi_params(
        self,
        spi_mode: SPIMode,
        cs_mode: SPICSMode,
        speed: int,
        word_len: int
    ) -> None:
        """
        Validate parameters for spi_set function.
        """
        # Constants
        speed_max_limit = int(100e6)
        speed_min_limit = 1
        word_len_list = [7, 8]

        # Input Limits Check
        if spi_mode not in SPIMode:
            raise ValueError(f"{spi_mode} is not a defined SPI mode.")
        if cs_mode not in SPICSMode:
            raise ValueError(f"{cs_mode} is not a defined CS mode.")
        if not (speed_min_limit <= speed <= speed_max_limit):
            raise ValueError(f"{speed} is out of range [{speed_min_limit}, {speed_max_limit}].")
        if word_len not in word_len_list:
            raise ValueError(f"Word length must be one of {word_len_list}. Current word length: {word_len}.")

    ### I2C ###

    def i2c_init(
        self,
        address: int = 0x80,
        dev_name: str = "/dev/i2c-0",
        fmode: bool = True
    ) -> None:
        """
        Configures the provided settings for I2C.

        Args:
            address (int, optional): I2C address of the device. Defaults to 0x80.
            dev_name (str, optional): I2C device name. Defaults to "/dev/i2c-0".
            fmode (bool, optional): Enable fast mode (400 kHz). Defaults to True.
        """
        self.tx_txt(f"I2C:DEV{address} \"{dev_name}\"")
        self.tx_txt(f"I2C:FMODE {'ON' if fmode else 'OFF'}")
        self.check_error()
    
    def i2c_get_settings(
        self
    ) -> List[str]:
        """Retrieves I2C settings from Red Pitaya.

        Returns:
            List[str]: ``[device, fmode]``.
        """
        settings = [
            self.txrx_txt("I2C:DEV?"),
            self.txrx_txt("I2C:FMODE?")
        ]
        return settings
    
    # def i2c_write_ioctl(
    #     self,
    #     data: np.ndarray
    # )
    #TODO add i2c_set()
    #TODO add i2c_get_settings()
    #TODO add i2c_write() - protocol IOctl Smbus
    #TODO add i2c_read() - protocol IOctl Smbus

    ### CAN ###

    #TODO add can_set(), can_get_settings(), can_write(), can_read()

    def can_data_split(self,
                       can_str: str
        ) -> Tuple[np.ndarray,  np.ndarray]:

        """
        Reorganizes the CAN string received from Red Pitaya into two NumPy
        arrays. The first one contains the CAN package information, the second
        one the CAN data.
        """
        can_str_split = can_str.split("{")
        can_data_start = np.array(can_str_split[0].split(","), dtype=np.int32)
        can_data = np.array(can_str_split[1].strip("}").split(","))

        return can_data_start, can_data

    ### DMM ###
    
    def dmm_calc_buffer_layout(
        self,
        acq_channels: Optional[List[int]] = None,
        acq_samples: Union[int, List[int]] = 0,
        gen_channels: Optional[List[int]] = None,
        gen_samples: Union[int, List[int]] = 0,
        pre_allocated: Optional[List[Tuple[int, int]]] = None,
    ) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Calculates non-overlapping, page-aligned DMM buffer addresses for both
        DMA (acquisition) and DMG (generation) channels from the shared DDR3
        memory region.

        Acquisition buffers are placed first, followed by generation buffers.
        Either or both sides may be specified; at least one must be provided.
        The same hardware constraints apply to both:

        - Minimum buffer size is 128 bytes (64 samples); smaller requests are
          rounded up.
        - Buffer size in samples is rounded up to the next multiple of 4
          (4 samples = 8 bytes).
        - Address spacing between consecutive buffers is rounded up to the next
          multiple of 4096 bytes (one DDR page).

        Args:
            acq_channels (List[int], optional): Acquisition channel numbers
                (e.g. ``[1, 2]``). Defaults to None (no acquisition buffers).
            acq_samples (int | List[int], optional): Samples per acquisition
                channel. Pass a single ``int`` for the same size on all
                channels, or a ``List[int]`` with one value per channel.
                Ignored when *acq_channels* is None. Defaults to 0.
            gen_channels (List[int], optional): Generation channel numbers.
                Defaults to None (no generation buffers allocated).
            gen_samples (int | List[int], optional): Samples per generation
                channel. Ignored when *gen_channels* is None. Defaults to 0.
            pre_allocated (List[Tuple[int, int]], optional): Regions already
                committed elsewhere as ``[(start_address, size_bytes), ...]``.
                The allocator begins after the highest end address found here,
                aligned to the next DDR page boundary. Useful when part of the
                DMM region is reserved by another subsystem or a previous call.
                Defaults to None.

        Returns:
            Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
                ``(acq_layout, gen_layout)`` where each entry is
                ``[(start_address, buffer_size_bytes), ...]`` in channel order.
                Either list may be empty if the corresponding channels argument
                was not provided.

        Raises:
            ValueError: If neither *acq_channels* nor *gen_channels* is
                provided, if the requested buffers exceed the available DMM
                memory, if a channel/samples list length mismatch is detected,
                or if *pre_allocated* regions fill the entire region.

        Warns:
            UserWarning: If the total allocation exceeds 90% of the available
                DMM memory (after subtracting any *pre_allocated* space).
        """
        if not acq_channels and not gen_channels:
            raise ValueError(
                "At least one of acq_channels or gen_channels must be provided."
            )

        WARN_THRESHOLD  = 0.90
        MIN_BUFFER_BYTES = 128   # hardware minimum: 128 bytes = 64 samples
        MIN_BLOCK_BYTES  = 4096  # one DDR page
        SAMPLE_ALIGNMENT = 4     # buffer size must be a multiple of 4 samples

        region_start, region_size = self.dma_get_region()

        # Determine the first usable address, skipping any pre-allocated regions
        if pre_allocated:
            highest_end = max(start + size for start, size in pre_allocated)
            # Align upward to the next DDR page boundary
            highest_end = math.ceil(highest_end / MIN_BLOCK_BYTES) * MIN_BLOCK_BYTES
            start_addr = max(region_start, highest_end)
        else:
            start_addr = region_start

        available = region_size - (start_addr - region_start)
        if available <= 0:
            raise ValueError(
                f"Pre-allocated regions consume the entire DMM region "
                f"({region_size} bytes); no space remains."
            )

        def _align(samples: int) -> Tuple[int, int]:
            """Return (buffer_size_bytes, offset_bytes) for one channel."""
            samples = math.ceil(samples / SAMPLE_ALIGNMENT) * SAMPLE_ALIGNMENT
            buf_bytes = samples * 2  # int16 = 2 bytes per sample
            if buf_bytes < MIN_BUFFER_BYTES:
                buf_bytes = MIN_BUFFER_BYTES
            offset = math.ceil(buf_bytes / MIN_BLOCK_BYTES) * MIN_BLOCK_BYTES
            return buf_bytes, offset

        def _expand(
            channels: List[int], samples: Union[int, List[int]]
        ) -> List[Tuple[int, int]]:
            """Expand and align a channel/samples specification."""
            if isinstance(samples, int):
                samples_list = [samples] * len(channels)
            else:
                if len(samples) != len(channels):
                    raise ValueError(
                        f"samples list has {len(samples)} entries but "
                        f"{len(channels)} channels were requested."
                    )
                samples_list = list(samples)
            return [_align(s) for s in samples_list]

        acq_aligned = _expand(acq_channels, acq_samples) if acq_channels else []
        gen_aligned  = _expand(gen_channels, gen_samples) if gen_channels else []

        total_required = sum(offset for _, offset in acq_aligned + gen_aligned)
        if total_required > available:
            raise ValueError(
                f"Insufficient DMM memory: requested layout requires "
                f"{total_required} bytes but only {available} bytes are available "
                f"({region_size} bytes total, "
                f"{start_addr - region_start} bytes pre-allocated)."
            )

        if total_required > available * WARN_THRESHOLD:
            warnings.warn(
                f"DMM memory usage is high: {total_required} of {available} bytes used "
                f"({100 * total_required / available:.1f}% of available DMM region).",
                UserWarning,
                stacklevel=2,
            )

        def _build_layout(
            aligned: List[Tuple[int, int]], addr: int
        ) -> Tuple[List[Tuple[int, int]], int]:
            layout = []
            for buf_bytes, offset in aligned:
                layout.append((addr, buf_bytes))
                addr += offset
            return layout, addr

        acq_layout, addr = _build_layout(acq_aligned, start_addr)
        gen_layout, _    = _build_layout(gen_aligned, addr)

        return acq_layout, gen_layout

    ### DMA ###
    
    def dma_get_region(
        self) -> Tuple[int, int]:
        """Retrieves the DMA memory region from Red Pitaya.

        Returns:
            Tuple[int, int]: ``(start_address, size_bytes)``.
        """
        start = int(self.txrx_txt("ACQ:AXI:START?"))
        size  = int(self.txrx_txt("ACQ:AXI:SIZE?"))
        return start, size

    def dma_calc_buffer_layout(
        self,
        channels: List[int],
        samples_per_channel: Union[int, List[int]],
    ) -> List[Tuple[int, int]]:
        """Calculates non-overlapping, page-aligned DMA buffer addresses.

        Thin wrapper around :meth:`dmm_calc_buffer_layout` for
        acquisition-only workflows. See :meth:`dmm_calc_buffer_layout` for full
        details, hardware constraints, and the ``pre_allocated`` option for
        mixed DMA/DMG setups.

        Args:
            channels (List[int]): Channel numbers to allocate (e.g. ``[1, 2]``).
            samples_per_channel (int | List[int]): Total samples per channel.

        Returns:
            List[Tuple[int, int]]: ``[(start_address, buffer_size_bytes), ...]``
                in the same order as *channels*.
        """
        acq_layout, _ = self.dmm_calc_buffer_layout(channels, samples_per_channel)
        return acq_layout

    def dma_check_regions(
        self,
        regions: List[Tuple[int, int]]
    ) -> None:
        """Validates that a list of DMA buffer regions do not overlap.

        Args:
            regions (List[Tuple[int, int]]): ``[(start_address, size_in_bytes), ...]``

        Raises:
            ValueError: If any two regions overlap.
        """
        sorted_regions = sorted(regions, key=lambda r: r[0])
        for i in range(len(sorted_regions) - 1):
            start_a, size_a = sorted_regions[i]
            start_b, _ = sorted_regions[i + 1]
            if start_a + size_a > start_b:
                raise ValueError(
                    f"DMA region overlap: region at 0x{start_a:x} (size {size_a} B) "
                    f"overlaps with region at 0x{start_b:x}."
                )


    def dma_set(
        self,
        decimation: int = 1,
        data_format: DataFormat = DataFormat.BIN,
        data_units: Units = Units.RAW,
        byte_order: ByteOrder = ByteOrder.LEND
    ) -> None:
        """Sets global DMA acquisition settings shared across all channels.

        Args:
            decimation (int, optional): Decimation factor. Defaults to 1.
            data_format (DataFormat, optional): Data format (ASCII or BIN). Defaults to DataFormat.BIN.
            data_units (Units, optional): Data units (RAW or VOLTS). Defaults to Units.RAW.
            byte_order (ByteOrder, optional): Byte order for binary data (LEND or BEND). Defaults to ByteOrder.LEND.
        """
        self.tx_txt(f"ACQ:AXI:DEC {decimation}")
        self.tx_txt(f"ACQ:AXI:DATA:Units {data_units.value}")
        self.tx_txt(f"ACQ:DATA:FORMAT {data_format.value}")
        self.tx_txt(f"ACQ:DATA:BYTE:ORDER {byte_order.value}")
        self.check_error()

    def dma_ch_set(
        self,
        channel: int,
        buffer_start_address: int,
        buffer_size: int,
        trigger_delay: int = 0,
    ) -> None:
        """Sets per-channel DMA acquisition settings.

        Args:
            channel (int): Input channel (1 or 2; 1–4 for STEMlab 125-14 4-Input).
            buffer_start_address (int): Start address of the DMA buffer in DDR3 RAM.
                Use :meth:`dma_calc_buffer_layout` to calculate non-overlapping addresses.
            buffer_size (int): Size of the DMA buffer in bytes.
            trigger_delay (int, optional): Trigger delay in samples. Defaults to 0.
        """
        #TODO should channel value be checked against board model (1-2 for STEMlab 125-14 and 1-4 for STEMlab 125-14 4-Input)?
        self.tx_txt(f"ACQ:AXI:SOUR{channel}:Trig:Dly {trigger_delay}")
        self.tx_txt(f"ACQ:AXI:SOUR{channel}:SET:Buffer {buffer_start_address},{buffer_size}")
        self.check_error()

    def dma_get_settings(self) -> List[str]:
        """Retrieves global DMA acquisition settings from Red Pitaya.

        Returns:
            List[str]: ``[decimation, data_units, data_format]``.
        """
        settings = [
            self.txrx_txt("ACQ:AXI:DEC?"),
            self.txrx_txt("ACQ:AXI:DATA:Units?"),
            self.txrx_txt("ACQ:DATA:FORMAT?"),
        ]
        return settings

    def dma_ch_get_settings(self, channel: int) -> List[str]:
        """Retrieves per-channel DMA acquisition settings from Red Pitaya.

        Returns:
            List[str]: ``[trigger_delay]``.
        """
        settings = [
            self.txrx_txt(f"ACQ:AXI:SOUR{channel}:Trig:Dly?"),
        ]
        return settings
    
    def dma_mode(
        self,
        channel: int,
        enable: bool
    ) -> None:
        """Enables or disables the DMA mode for the specified channel."""
        self.tx_txt(f"ACQ:AXI:SOUR{channel}:ENable {'ON' if enable else 'OFF'}")
        self.check_error()
        return


    def dma_data(
        self,
        chan: int,
        pos: int,
        size: int,
        data_format: Optional[DataFormat] = None,
        data_units: Optional[Units] = None,
        byte_order: Optional[ByteOrder] = None,
    ) -> np.ndarray:
        """Reads ``size`` samples from the DMA buffer starting at ``pos``.

        When *data_format*, *data_units*, and *byte_order* are supplied (i.e.
        the same values passed to :meth:`dma_set`), no extra SCPI queries are
        issued and the call reduces to a single round-trip. If any parameter is
        omitted (``None``) its value is queried from the board instead, which
        is safe but adds latency.

        Args:
            chan (int): Input channel (1 or 2; 1–4 for STEMlab 125-14 4-Input).
            pos (int): Start position in the circular buffer (see
                :meth:`dma_get_trig_pos`).
            size (int): Number of samples to read.
            data_format (DataFormat, optional): Expected data format
                (``DataFormat.BIN`` or ``DataFormat.ASCII``). Defaults to
                ``None`` (queried from board).
            data_units (Units, optional): Expected data units
                (``Units.VOLTS`` or ``Units.RAW``). Defaults to ``None``
                (queried from board).
            byte_order (ByteOrder, optional): Byte order for binary data
                (``ByteOrder.LEND`` or ``ByteOrder.BEND``). Only used when
                *data_format* is ``DataFormat.BIN``. Defaults to ``None``
                (queried from board).

        Returns:
            np.ndarray: Captured data as float64.
        """
        units_str  = data_units.value   if data_units   is not None else self.txrx_txt("ACQ:AXI:DATA:UNITS?")
        format_str = data_format.value  if data_format  is not None else self.txrx_txt("ACQ:DATA:FORMAT?")

        self.tx_txt(f"ACQ:AXI:SOUR{chan}:DATA:Start:N? {pos},{size}")

        if format_str == "BIN":
            buff_byte = self.rx_arb()
            if not isinstance(buff_byte, bytes):
                raise ValueError("Failed to receive binary DMA data")

            if byte_order is not None:
                order_str = byte_order.value
            else:
                try:
                    order_str = self.txrx_txt("ACQ:DATA:BYTE:ORDER?").strip()
                except Exception:
                    order_str = ByteOrder.BEND.value    # big-endian is the board default

            if order_str == ByteOrder.LEND.value:
                float_dtype, int_dtype = "<f4", "<i2"
            else:
                float_dtype, int_dtype = ">f4", ">i2"

            if units_str == Units.VOLTS.value:
                buff = np.frombuffer(buff_byte, dtype=float_dtype)
            else:  # RAW
                buff = np.frombuffer(buff_byte, dtype=int_dtype)
            buff = buff.astype(np.float64)
        else:
            buff_string = self.rx_txt().strip("{}\n\r").replace("  ", "").split(",")
            buff = np.array(buff_string, dtype=np.float64)

        self.check_error()
        return buff



    ### DMG ###

    def dmg_get_region(
        self) -> Tuple[int, int]:
        """Retrieves the DMG memory region from Red Pitaya.

        Returns:
            Tuple[int, int]: ``(start_address, size_bytes)``.
        """
        start = int(self.txrx_txt("GEN:AXI:START?"))
        size  = int(self.txrx_txt("GEN:AXI:SIZE?"))
        return start, size

    def dmg_calc_buffer_layout(
        self,
        channels: List[int],
        samples_per_channel: Union[int, List[int]],
    ) -> List[Tuple[int, int]]:
        """Calculates non-overlapping, page-aligned DMG buffer regions.

        Thin wrapper around :meth:`dmm_calc_buffer_layout` for generation-only
        workflows. See :meth:`dmm_calc_buffer_layout` for full details and the
        ``pre_allocated`` option for mixed DMA/DMG setups.

        Args:
            channels (List[int]): Channel numbers to allocate (e.g. ``[1, 2]``).
            num_samples (int): Number of waveform samples per channel.

        Returns:
            List[Tuple[int, int]]: ``[(start_address, buffer_size_bytes), ...]``
                in the same order as *channels*. Pass directly to
                :meth:`dmg_ch_set`.
        """
        _, gen_layout = self.dmm_calc_buffer_layout(
            gen_channels=channels,
            gen_samples=samples_per_channel,
        )
        return gen_layout


    def dmg_ch_set(
        self,
        channel: int,
        start_address: int,
        buffer_size_bytes: int,
        decimation: int = 1,
    ) -> None:
        """Reserves DDR memory and sets the decimation for one DMG channel.

        Combines the ``SOUR<n>:AXI:RESERVE`` and ``SOUR<n>:AXI:DEC`` commands.
        Use :meth:`dmg_calc_buffer_layout` or :meth:`dmm_calc_buffer_layout` to
        obtain non-overlapping ``(start_address, buffer_size_bytes)`` values.

        Args:
            channel (int): Output channel (1 or 2).
            start_address (int): Start address of the buffer in DDR3 RAM.
            buffer_size_bytes (int): Buffer size in bytes (int16 samples × 2).
            decimation (int, optional): Decimation factor. Defaults to 1.
        """
        end_address = start_address + buffer_size_bytes
        self.tx_txt(f"SOUR{channel}:AXI:RESERVE {start_address},{end_address}")
        self.tx_txt(f"SOUR{channel}:AXI:DEC {decimation}")
        self.check_error()

    def dmg_write_waveform(
        self,
        chan: int,
        data: np.ndarray,
        offset: int = 0,
        amplitude: float = 1.0,
        chunk_size: int = 2**14,
    ) -> None:
        """Writes a waveform array into the Deep Memory Generation buffer.

        The input *data* is automatically normalised to the ``[-1, 1]``
        full-scale range by dividing by its peak absolute value before
        transmission, so any amplitude scale is accepted. A zero-only array
        is sent as-is. Large arrays are sent in chunks so the SCPI server
        message-size limit is never exceeded.

        Call :meth:`dmg_apply_calib` after writing to apply DAC calibration.

        Args:
            chan (int): Output channel (1 or 2).
            data (np.ndarray): Waveform samples. Any floating-point scale is
                accepted; the array is normalised to ``[-1, 1]`` internally.
            offset (int): Sample offset into the reserved region for writing
                data in portions. Default: ``0``.
            amplitude (float): Output amplitude as a fraction of full scale,
                in the range ``(0, 1]``. Default: ``1.0``.
            chunk_size (int): Maximum samples per SCPI message. Default: 2**14.
        """
        amplitude = float(np.clip(amplitude, 0.0, 1.0))
        # float32 is sufficient for a 14-bit DAC and halves memory vs float64
        data = np.asarray(data, dtype=np.float32)
        max_abs = float(np.max(np.abs(data)))
        if max_abs > 0.0:
            # single multiply: normalise and scale in one vectorised pass
            data = np.clip(data * (amplitude / max_abs), -1.0, 1.0)
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            self.tx_txt(
                f"SOUR{chan}:AXI:OFFSET{offset + i}:DATA{len(chunk)} "
                + ",".join(np.char.mod("%.6f", chunk))
            )
        self.check_error()

    def dmg_apply_calib(self, channel: int) -> None:
        """Applies DAC calibration to the DMG buffer of the specified channel.

        Must be called after :meth:`dmg_write_waveform` and before starting
        generation.

        Args:
            channel (int): Output channel (1 or 2).
        """
        self.tx_txt(f"SOUR{channel}:AXI:SET:CALIB")
        self.check_error()

    def dmg_mode(
        self,
        channel: int,
        enable: bool,
    ) -> None:
        """Enables or disables Deep Memory Generation mode for one channel.

        Args:
            channel (int): Output channel (1 or 2).
            enable (bool): True to enable, False to disable.
        """
        self.tx_txt(f"SOUR{channel}:AXI:ENable {'ON' if enable else 'OFF'}")
        self.check_error()


    def dmg_release(self, channel: int) -> None:
        """Releases the reserved DDR memory for the specified DMG channel.

        Should be called when generation is complete or when reconfiguring
        the buffer layout.

        Args:
            channel (int): Output channel (1 or 2).
        """
        self.tx_txt(f"SOUR{channel}:AXI:RELEASE")
        self.check_error()


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

    def sre(self):
        """Service Request Enable Command"""
        #TODO: IEEE 488.2 requires a mask value argument: *SRE <value>. The underlying SCPI command handling needs to be updated by developers to accept the value.
        return self.tx_txt('*SRE')

    def sre_q(self):
        """Service Request Enable Query"""
        return self.txrx_txt('*SRE?')

    def stb_q(self) -> Optional[str]:
        """Read Status Byte Query.
        
        Returns:
            Current status byte value or None if error
        """
        try:
            return self.txrx_txt('*STB?')
        except (ConnectionError, socket.error):
            return None

# :SYSTem
    def err_c(self) -> str:
        """Error count query.
        
        Returns:
            Number of errors in error queue
        """
        return self.txrx_txt('SYSTem:ERRor:COUNt?')

    def err_n(self) -> Optional[str]:
        """Error next query.
        
        Returns:
            Next error from error queue or None if error
        """
        try:
            return self.txrx_txt('SYSTem:ERRor:NEXT?')
        except (ConnectionError, socket.error):
            return None
