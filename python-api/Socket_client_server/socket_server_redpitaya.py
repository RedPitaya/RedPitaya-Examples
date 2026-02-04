#!/usr/bin/env python3
"""
High-Performance TCP Server for Red Pitaya
==========================================
Optimized for fast data transfer of large datasets from Red Pitaya to client.
Uses DMA (AXI) acquisition for maximum performance with multi-channel support.

Usage:
    Run this script on the Red Pitaya board:
    python3 socket_server_redpitaya.py
"""

import socket
import struct
import time
import numpy as np
import signal
import errno
import sys
import rp

# Server configuration
HOST = '0.0.0.0'  # Listen on all network interfaces
PORT = 5000       # Port to listen on
BUFFER_SIZE = 1048576   # 1 MB

# Protocol commands (single byte for efficiency)
CMD_ACQUIRE = b'\x01'
CMD_CONFIG_DEC = b'\x02'
CMD_CONFIG_TRIG = b'\x03'
CMD_STATUS = b'\x04'
CMD_QUIT = b'\xFF'

# Red Pitaya acquisition configuration
DEBUG = False  # Set to True for debug output

# Channel configuration
ch1 = rp.RP_CH_1
ch2 = rp.RP_CH_2
ch3 = rp.RP_CH_3
CHANNELS = [ch1, ch2, ch3]  # Channels to acquire
CH_NUM = len(CHANNELS)

# Acquisition parameters (can be modified via commands)
DEC = 1                     # Decimation factor (powers of 2 up to 16, then any integer)
TRIG_LVL = 0.2              # Trigger level in volts
TRIG_DLY = 0                # Trigger delay
CHANNEL_SAMPLES_SIZE = int(12.8 * 1e6) # Samples per channel - must be multiple of 8
AXI_MIN_BLOCK_SIZE = 4096   # Minimum AXI block size (must be multiple of 4096)
AXI_BLOCK_SIZE = ((2 * CHANNEL_SAMPLES_SIZE + AXI_MIN_BLOCK_SIZE - 1) // AXI_MIN_BLOCK_SIZE) * AXI_MIN_BLOCK_SIZE

# Global variables for Red Pitaya state
rp_initialized = False
dma_start_addr = 0
dma_full_size = 0

# Statistics tracking
stats = {
    'acquisitions': 0,
    'total_acq_time': 0.0,
    'total_transfer_time': 0.0,
    'total_bytes_sent': 0,
    'errors': 0
}


def setup_red_pitaya():
    """Initialize and configure Red Pitaya for multi-channel acquisition"""
    global rp_initialized, dma_start_addr, dma_full_size
    
    try:
        rp.rp_Init()
        rp_initialized = True
        
        # Get memory information
        memory = rp.rp_AcqAxiGetMemoryRegion()
        dma_start_addr = memory[1]
        dma_full_size = memory[2]
        
        if DEBUG:
            print(f"DMA Memory: start=0x{dma_start_addr:x}, size={dma_full_size}")
        
        return True
    except Exception as e:
        print(f"Error initializing Red Pitaya: {e}")
        return False


def configure_acquisition():
    """Configure acquisition parameters for all channels"""
    try:
        # Set decimation factor
        rp.rp_AcqAxiSetDecimationFactor(DEC)
        
        # Set trigger parameters
        rp.rp_AcqSetTriggerLevel(rp.RP_T_CH_1, TRIG_LVL)  # Trigger on CH1

        if DEBUG:
            print(f"Using AXI block size: {AXI_BLOCK_SIZE} bytes")
        
        # Configure each channel
        buffer_offset = dma_start_addr
        for i, channel in enumerate(CHANNELS):
            if DEBUG:
                print(f"Channel {i+1}: buffer at {buffer_offset}")

            rp.rp_AcqAxiSetTriggerDelay(channel, CHANNEL_SAMPLES_SIZE)
            rp.rp_AcqAxiSetBufferSamples(channel, buffer_offset, CHANNEL_SAMPLES_SIZE)
            rp.rp_AcqAxiEnable(channel, True)
            buffer_offset = buffer_offset + (i+1) * AXI_BLOCK_SIZE
        
        return True
    except Exception as e:
        print(f"Error configuring acquisition: {e}")
        return False


def process_channel_data(memory_region, channel_idx, output_buffer):
    """
    Process data from a single channel memory region directly into output buffer.
    No intermediate copies - writes directly to pre-allocated buffer.
    """
    if memory_region[0] != 0:  # Check for errors
        if DEBUG:
            print(f"Error reading channel {channel_idx + 1} data: {memory_region[0]}")
        output_buffer.fill(0)  # Zero out on error
        return False
    
    # Get direct view of output buffer as bytes
    buffer_view = output_buffer.view(np.uint8)
    offset = 0
    
    # Copy spans directly into buffer without intermediate allocation
    for span in memory_region[1]:
        span_len = min(len(span), len(buffer_view) - offset)
        if span_len > 0:
            buffer_view[offset:offset + span_len] = span[:span_len]
            offset += span_len
    
    # Zero remaining if incomplete
    if offset < len(buffer_view):
        buffer_view[offset:].fill(0)
    
    return True


def acquire_data():
    """
    Perform fast AXI acquisition on all configured channels.
    Returns (numpy array, acquisition_time) tuple.
    Array is allocated once and filled directly - zero copies.
    """
    try:
        acq_start_time = time.perf_counter()
        
        # Pre-allocate array for all channels - this is the ONLY allocation
        data_array = np.zeros((CH_NUM, CHANNEL_SAMPLES_SIZE), dtype=np.int16)
        
        # Start acquisition and set trigger
        rp.rp_AcqStart()
        rp.rp_AcqSetTriggerSrc(rp.RP_TRIG_SRC_CHA_PE)  # IN1 rising edge

        # Wait for trigger and data acquisition
        timeout = time.perf_counter() + 10.0  # 10s max wait
        while rp.rp_AcqAxiGetBufferFillState(rp.RP_CH_1)[1] == 0 and time.perf_counter() < timeout:
            pass
        
        if time.perf_counter() >= timeout:
            raise TimeoutError("Trigger wait timed out")

        rp.rp_AcqStop()

        # Get trigger positions for all channels
        trigger_positions = [rp.rp_AcqAxiGetWritePointerAtTrig(channel)[1] for channel in CHANNELS]

        # Read data from all channels
        memory_regions = [rp.rp_AcqAxiGetDataRawDirect(channel, trigger_positions[i], CHANNEL_SAMPLES_SIZE) 
                         for i, channel in enumerate(CHANNELS)]

        # Process data directly into pre-allocated buffer - no copies
        for i, memory_region in enumerate(memory_regions):
            process_channel_data(memory_region, i, data_array[i])

        acq_time = time.perf_counter() - acq_start_time

        return data_array, acq_time
        
    except Exception as e:
        if DEBUG:
            print(f"Error during acquisition: {e}")
        return None, 0.0


def print_statistics():
    """Print accumulated statistics"""
    if stats['acquisitions'] == 0:
        print("No acquisitions performed")
        return
    
    avg_acq_time = stats['total_acq_time'] / stats['acquisitions']
    avg_transfer_time = stats['total_transfer_time'] / stats['acquisitions']
    total_mb = stats['total_bytes_sent'] / (1024 * 1024)
    
    print("\n" + "=" * 60)
    print("Session Statistics:")
    print("=" * 60)
    print(f"  Total acquisitions:     {stats['acquisitions']}")
    print(f"  Errors:                 {stats['errors']}")
    print(f"  Total data transferred: {total_mb:.2f} MB")
    print(f"  Avg acquisition time:   {avg_acq_time*1000:.3f} ms")
    print(f"  Avg sendall() time:     {avg_transfer_time*1000:.3f} ms")
    print(f"\n  Note: sendall() time != actual network transfer time.")
    print(f"  Client-side measurements are accurate for throughput.")
    print("=" * 60 + "\n")


def cleanup_red_pitaya():
    """Cleanup Red Pitaya resources"""
    global rp_initialized
    
    try:
        if rp_initialized:
            for channel in CHANNELS:
                rp.rp_AcqAxiEnable(channel, False)
            rp.rp_Release()
            rp_initialized = False
            print("Red Pitaya resources released")
    except Exception as e:
        print(f"Error during cleanup: {e}")


def send_metadata(conn):
    """
    Send acquisition metadata once at connection start.
    Client only needs this information once since shape/dtype never change.
    """
    try:
        dtype_str = 'int16'
        dtype_bytes = dtype_str.encode('utf-8')
        
        # Send metadata packet
        conn.sendall(struct.pack('I', len(dtype_bytes)))
        conn.sendall(dtype_bytes)
        conn.sendall(struct.pack('III', 2, CH_NUM, CHANNEL_SAMPLES_SIZE))  # ndim, dim0, dim1
        return True
    except Exception as e:
        if DEBUG:
            print(f"Error sending metadata: {e}")
        return False


def send_data_fast(conn, data):
    """
    Send raw data only - no metadata overhead.
    Just data size + raw bytes. Minimal protocol overhead.
    Returns (success, transfer_time, bytes_sent) tuple.
    """
    try:
        start_time = time.perf_counter()
        
        data_size = data.nbytes
        
        # Send only data size (4 bytes) - use uint32 since size is always < 4GB
        conn.sendall(struct.pack('I', data_size))
        
        # Send raw data using buffer protocol - zero copy
        if not data.flags['C_CONTIGUOUS']:
            data = np.ascontiguousarray(data)
        
        data_view = memoryview(data)
        bytes_sent = 0
        
        while bytes_sent < data_size:
            chunk_size = min(BUFFER_SIZE, data_size - bytes_sent)
            chunk = data_view[bytes_sent:bytes_sent + chunk_size]
            conn.sendall(chunk)
            bytes_sent += chunk_size
        
        transfer_time = time.perf_counter() - start_time
        
        return True, transfer_time, data_size
        
    except Exception as e:
        if DEBUG:
            print(f"Error sending data: {e}")
        return False, 0.0, 0


def bind_with_retry(server_socket, max_retries=3, retry_delay=2):
    """Attempt to bind socket with retry logic for port-in-use scenarios."""
    for attempt in range(max_retries):
        try:
            server_socket.bind((HOST, PORT))
            return True
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                print(f"Port {PORT} is already in use (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"Waiting {retry_delay}s for existing server to close...")
                    time.sleep(retry_delay)
                    # Try to force socket reuse
                    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    if hasattr(socket, 'SO_REUSEPORT'):
                        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                else:
                    print(f"Failed to bind after {max_retries} attempts.")
                    print("Tip: Kill existing server process or wait for TIME_WAIT to expire.")
                    return False
            else:
                print(f"Bind error: {e}")
                return False
    return False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\nReceived shutdown signal, cleaning up...")
    cleanup_red_pitaya()
    sys.exit(0)


def run_server():
    """Main server loop - waits for client connections and sends data."""
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize Red Pitaya before starting server
    print("Initializing Red Pitaya...")
    if not setup_red_pitaya():
        print("Failed to initialize Red Pitaya. Exiting.")
        return
    
    print("Configuring acquisition...")
    if not configure_acquisition():
        print("Failed to configure acquisition. Exiting.")
        cleanup_red_pitaya()
        return
    
    print("Red Pitaya ready!")
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Enable address reuse to handle rapid restart scenarios
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Set linger option to force immediate close
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
    
    # Optimize socket for throughput
    server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's algorithm
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, BUFFER_SIZE * 4)  # Increase send buffer
    
    try:
        # Try to bind with retry logic
        if not bind_with_retry(server_socket):
            server_socket.close()
            cleanup_red_pitaya()
            return
        server_socket.listen(1)
        print(f"Server listening on {HOST}:{PORT}")
        print(f"Buffer size: {BUFFER_SIZE} bytes")
        print(f"Acquisition: {CH_NUM} channels, {CHANNEL_SAMPLES_SIZE} samples each")
        print("Waiting for client connection...")
        
        while True:
            conn, addr = server_socket.accept()
            print(f"Connected by {addr}")
            
            # Reset statistics for new connection
            stats['acquisitions'] = 0
            stats['total_acq_time'] = 0.0
            stats['total_transfer_time'] = 0.0
            stats['total_bytes_sent'] = 0
            stats['errors'] = 0
            
            try:
                # Optimize client socket
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                conn.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, BUFFER_SIZE * 4)
                
                # Send metadata once at connection start
                if not send_metadata(conn):
                    print("Failed to send metadata")
                    conn.close()
                    continue
                
                while True:
                    # Read single-byte command
                    cmd = conn.recv(1)
                    
                    if not cmd or cmd == CMD_QUIT:
                        break
                    
                    elif cmd == CMD_ACQUIRE:
                        # Perform Red Pitaya acquisition
                        start_time_full = time.perf_counter()
                        try:
                            # Acquire data using AXI
                            data, acq_time = acquire_data()
                            
                            if data is None:
                                # Send error marker (size = 0)
                                conn.sendall(struct.pack('I', 0))
                                stats['errors'] += 1
                                continue
                            
                            # Send data (just size + raw bytes)
                            success, transfer_time, bytes_sent = send_data_fast(conn, data)
                            
                            if not success:
                                stats['errors'] += 1
                                break

                            transfer_time_full = time.perf_counter() - start_time_full
                            print(f"Full acquisition + transfer time: {transfer_time_full:.6f} seconds")
                            
                            # Update statistics
                            stats['acquisitions'] += 1
                            stats['total_acq_time'] += acq_time
                            stats['total_transfer_time'] += transfer_time
                            stats['total_bytes_sent'] += bytes_sent
                            
                        except Exception as e:
                            if DEBUG:
                                print(f"Acquisition error: {e}")
                            # Send error marker
                            conn.sendall(struct.pack('I', 0))
                            stats['errors'] += 1
                    
                    elif cmd == CMD_CONFIG_DEC:
                        # Read 4-byte decimation value
                        try:
                            dec_bytes = conn.recv(4)
                            if len(dec_bytes) == 4:
                                global DEC
                                DEC = struct.unpack('I', dec_bytes)[0]
                                conn.sendall(b'\x00')  # ACK
                            else:
                                conn.sendall(b'\xFF')  # NACK
                        except:
                            conn.sendall(b'\xFF')  # NACK
                    
                    elif cmd == CMD_CONFIG_TRIG:
                        # Read 4-byte float trigger level
                        try:
                            trig_bytes = conn.recv(4)
                            if len(trig_bytes) == 4:
                                global TRIG_LVL
                                TRIG_LVL = struct.unpack('f', trig_bytes)[0]
                                conn.sendall(b'\x00')  # ACK
                            else:
                                conn.sendall(b'\xFF')  # NACK
                        except:
                            conn.sendall(b'\xFF')  # NACK
                    
                    elif cmd == CMD_STATUS:
                        # Send current config as binary
                        status_data = struct.pack('IIIf', CH_NUM, CHANNEL_SAMPLES_SIZE, DEC, TRIG_LVL)
                        conn.sendall(status_data)
                    
                    else:
                        # Unknown command - send NACK
                        conn.sendall(b'\xFF')
            
            except Exception as e:
                if DEBUG:
                    print(f"Error handling client: {e}")
                stats['errors'] += 1
            
            finally:
                conn.close()
                print_statistics()
    
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    except Exception as e:
        print(f"\nServer error: {e}")
    finally:
        try:
            server_socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        server_socket.close()
        cleanup_red_pitaya()
        print("Server closed")


if __name__ == "__main__":
    print("=" * 60)
    print("Red Pitaya High-Performance TCP Server")
    print("=" * 60)
    run_server()
