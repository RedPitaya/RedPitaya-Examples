#!/usr/bin/env python3
"""
High-Performance TCP Client for Red Pitaya - Optimized Binary Protocol
=======================================================================
Minimal overhead binary protocol for maximum throughput.
Metadata sent once at connection, then pure binary data transfer.

Usage:
    python socket_client_fast.py <redpitaya_ip> [benchmark]
"""

import socket
import struct
import sys
import time
import numpy as np

# Client configuration
PORT = 5000
BUFFER_SIZE = 1048576   # 1 MB
TIMEOUT = 30.0

# Protocol commands
CMD_ACQUIRE = b'\x01'
CMD_CONFIG_DEC = b'\x02'
CMD_CONFIG_TRIG = b'\x03'
CMD_STATUS = b'\x04'
CMD_QUIT = b'\xFF'


def recv_exact(sock, num_bytes):
    """Receive exactly num_bytes from socket."""
    data = b''
    while len(data) < num_bytes:
        chunk = sock.recv(min(num_bytes - len(data), BUFFER_SIZE))
        if not chunk:
            return None
        data += chunk
    return data


def receive_metadata(sock):
    """Receive metadata once at connection start."""
    try:
        # Receive dtype
        dtype_len_data = recv_exact(sock, 4)
        if not dtype_len_data:
            return None, None
        dtype_len = struct.unpack('I', dtype_len_data)[0]
        
        dtype_bytes = recv_exact(sock, dtype_len)
        if not dtype_bytes:
            return None, None
        dtype_str = dtype_bytes.decode('utf-8')
        
        # Receive shape (ndim + dimensions)
        shape_data = recv_exact(sock, 12)
        if not shape_data:
            return None, None
        ndim, dim0, dim1 = struct.unpack('III', shape_data)
        
        return dtype_str, (dim0, dim1)
    except Exception as e:
        print(f"Error receiving metadata: {e}")
        return None, None


def receive_data_fast(sock, dtype, shape):
    """Receive raw data - minimal overhead."""
    try:
        # Receive data size
        size_data = recv_exact(sock, 4)
        if not size_data:
            return None
        data_size = struct.unpack('I', size_data)[0]
        
        if data_size == 0:
            return None  # Error marker
        
        # Receive data
        data_bytes = recv_exact(sock, data_size)
        if not data_bytes:
            return None
        
        # Reconstruct numpy array
        data = np.frombuffer(data_bytes, dtype=dtype).reshape(shape)
        return data
        
    except Exception as e:
        print(f"Error receiving data: {e}")
        return None


def run_client(host):
    """Interactive client mode."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE * 4)
    
    try:
        print(f"Connecting to {host}:{PORT}...")
        sock.connect((host, PORT))
        print(f"Connected\n")
        
        # Receive metadata
        dtype, shape = receive_metadata(sock)
        if dtype is None:
            print("Failed to receive metadata")
            return
        print(f"Metadata: dtype={dtype}, shape={shape}\n")
        
        print("Commands: ACQUIRE | STATUS | CONFIG:DEC:<n> | CONFIG:TRIG:<v> | QUIT\n")
        
        while True:
            cmd = input("> ").strip()
            if not cmd:
                continue
            
            if cmd == "QUIT":
                sock.sendall(CMD_QUIT)
                break
            
            elif cmd == "ACQUIRE":
                start_time = time.perf_counter()
                sock.sendall(CMD_ACQUIRE)
                data = receive_data_fast(sock, dtype, shape)
                if data is not None:
                    print(f"Shape: {data.shape}")
                    for ch in range(data.shape[0]):
                        print(f"  CH{ch+1}: min={data[ch].min()}, max={data[ch].max()}, mean={data[ch].mean():.1f}")
                else:
                    print("Failed\n")
                
                elapsed = time.perf_counter() - start_time
                print(f"Acquisition time: {elapsed*1000:.3f} ms\n")
            
            elif cmd.startswith("CONFIG:DEC:"):
                value = int(cmd.split(':')[2])
                sock.sendall(CMD_CONFIG_DEC + struct.pack('I', value))
                ack = sock.recv(1)
                print("OK" if ack == b'\x00' else "FAILED")
            
            elif cmd.startswith("CONFIG:TRIG:"):
                value = float(cmd.split(':')[2])
                sock.sendall(CMD_CONFIG_TRIG + struct.pack('f', value))
                ack = sock.recv(1)
                print("OK" if ack == b'\x00' else "FAILED")
            
            elif cmd == "STATUS":
                sock.sendall(CMD_STATUS)
                status = sock.recv(16)
                ch, samp, dec, trig = struct.unpack('IIIf', status)
                print(f"Channels={ch}, Samples={samp}, Dec={dec}, Trig={trig}V")
            
            else:
                print("Unknown command")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()


def benchmark_mode(host, iterations=100):
    """Benchmark mode - measures throughput."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE * 4)
    
    try:
        print(f"Connecting to {host}:{PORT}...")
        sock.connect((host, PORT))
        print("Connected\n")
        
        # Receive metadata
        dtype, shape = receive_metadata(sock)
        if dtype is None:
            print("Failed to receive metadata")
            return
        print(f"Metadata: dtype={dtype}, shape={shape}\n")
        
        data_size = np.dtype(dtype).itemsize * shape[0] * shape[1]
        
        print(f"Benchmark: {iterations} acquisitions")
        print(f"Data size per acquisition: {data_size:,} bytes ({data_size/(1024*1024):.3f} MB)")
        print("=" * 60)
        
        times = []
        total_start = time.perf_counter()
        
        for i in range(iterations):
            sock.sendall(CMD_ACQUIRE)
            
            start = time.perf_counter()
            data = receive_data_fast(sock, dtype, shape)
            elapsed = time.perf_counter() - start
            
            if data is not None:
                times.append(elapsed)
                throughput = (data_size / (1024 * 1024)) / elapsed
                print(f"  {i+1:2d}: {elapsed*1000:6.3f} ms ({throughput:6.2f} MB/s)")
            else:
                print(f"  {i+1:2d}: FAILED")
                break
        
        total_time = time.perf_counter() - total_start
        
        # Send quit
        sock.sendall(CMD_QUIT)
        
        # Summary
        if times:
            total_mb = data_size * len(times) / (1024 * 1024)
            print("\n" + "=" * 60)
            print("Results:")
            print(f"  Acquisitions:     {len(times)}")
            print(f"  Total time:       {total_time:.3f} s")
            print(f"  Total data:       {total_mb:.3f} MB")
            print(f"  Avg time:         {np.mean(times)*1000:.3f} ms")
            print(f"  Min time:         {np.min(times)*1000:.3f} ms")
            print(f"  Max time:         {np.max(times)*1000:.3f} ms")
            print(f"  Std dev:          {np.std(times)*1000:.3f} ms")
            print(f"  Avg throughput:   {total_mb / sum(times):.2f} MB/s")
            print(f"  Peak throughput:  {(data_size/(1024*1024)) / np.min(times):.2f} MB/s")
            print("=" * 60)
        
    except Exception as e:
        print(f"Benchmark error: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Red Pitaya Fast TCP Client (Binary Protocol)")
    print("=" * 60)
    print()
    
    if len(sys.argv) < 2:
        print("Usage: python socket_client_fast.py <host> [benchmark]")
        sys.exit(1)
    
    host = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2] == "benchmark":
        benchmark_mode(host, iterations=100)
    else:
        run_client(host)
