High-Performance Red Pitaya TCP Data Acquisition
=================================================

This folder contains a high-performance client-server system for fast data acquisition 
and transfer from Red Pitaya boards to a computer via TCP/IP.

Overview
--------
The code demonstrates the fastest possible data acquisition in Python using the 
rp_AcqAxiGetDataRawDirect function combined with optimized TCP/IP transfer.
Designed to transfer ~80 MB of data with minimal overhead and maximum throughput.


Files
-----
- socket_server_redpitaya.py : TCP server running on Red Pitaya board
- socket_client_fast.py      : TCP client running on the computer
- README.txt                  : This file


Main Ideas & Optimizations
---------------------------

SERVER (socket_server_redpitaya.py):
------------------------------------
1. Zero-Copy DMA Acquisition
   - Uses rp_AcqAxiGetDataRawDirect for direct memory access
   - No intermediate buffer copies - data flows directly to numpy arrays
   - Processes all channels (3x 12.8M samples) with minimal overhead

2. Minimal Protocol Overhead
   - Single-byte commands for efficiency (0x01=ACQUIRE, 0xFF=QUIT, etc.)
   - Metadata sent once at connection start, then pure binary data transfer
   - Only 4 bytes header per data packet (just the size)

3. TCP Optimization
   - 1 MB buffer size (adjust depending on total data lenght)
   - TCP_NODELAY to disable Nagle's algorithm (lower latency)
   - Large send buffer (4x buffer size) for better throughput
   - Chunked sending with memoryview for zero-copy transmission

4. Robust Operation
   - Automatic retry logic for port binding (handles rapid restarts)
   - Signal handlers for graceful shutdown on SSH disconnect
   - SO_REUSEADDR + SO_LINGER for immediate socket reuse
   - Comprehensive statistics tracking (acquisitions, errors, throughput)


CLIENT (socket_client_fast.py):
--------------------------------
1. Efficient Data Reception
   - recv_exact() ensures complete data packets are received
   - 1 MB receive buffer (to reduce system calls)
   - Large socket receive buffer (4x buffer size)

2. Metadata Caching
   - Receives dtype and shape once at connection
   - All subsequent transfers are pure binary data
   - numpy array reconstruction from raw bytes with no copies

3. Dual Operation Modes
   - Interactive mode: Manual commands (ACQUIRE, STATUS, CONFIG, QUIT)
   - Benchmark mode: Automated throughput testing with statistics
   
4. Performance Measurement
   - Accurate timing for each acquisition
   - Throughput calculation in MB/s
   - Statistics: min/max/avg times, total data, peak throughput


Protocol Flow
-------------
1. Client connects to server (port 5000)
2. Server sends metadata: dtype (int16) + shape (channels, samples)
3. Client sends single-byte commands
4. For ACQUIRE command:
   - Server performs DMA acquisition on Red Pitaya
   - Server sends: [4 bytes size][raw binary data]
   - Client receives and reconstructs numpy array
5. Repeat acquisitions with minimal overhead
6. Client sends QUIT command to disconnect


Typical Performance (during test run)
--------------------------------------
- Data size: ~76.8 MB per acquisition (3 channels × 12.8M samples × 2 bytes)
- Throughput: 45.3+ MB/s (depending on network conditions)
- Acquisition time: ~1616 ms (acquisition + transfer)
- Buffer size: 1 MB (close to optimal for this data size)

Test results measured on the computer:

Metadata: dtype=int16, shape=(3, 12800000)

Benchmark: 100 acquisitions
Data size per acquisition: 76,800,000 bytes (73.242 MB)

Results (computer side):

  Acquisitions:     100
  Total time:       161.730 s
  Total data:       7324.219 MB
  Avg time:         1616.965 ms
  Min time:         1537.147 ms
  Max time:         2123.366 ms
  Std dev:          74.352 ms
  Avg throughput:   45.30 MB/s
  Peak throughput:  47.65 MB/s

Statistics (Red Pitaya side):

  Total acquisitions:     100
  Errors:                 0
  Total data transferred: 7324.22 MB
  Avg acquisition time:   615.556 ms
  Avg sendall() time:     842.390 ms

Note:   The test were performed with the input trigger set to CH1_PE.
        The trigger waveform was 10 kHz sine wave.
        Web interface (nginx) was disabled during the test.


Usage
-----
On Red Pitaya:
    python3 socket_server_redpitaya.py

On Computer (Interactive):
    python socket_client_fast.py rp-f0b506.local
    > ACQUIRE
    > STATUS
    > QUIT

On Computer (Benchmark):
    python socket_client_fast.py rp-f0b506.local benchmark


Key Takeaways
-------------
- Zero-copy techniques minimize memory operations
- Large buffers reduce system call overhead for big transfers
- Minimal protocol design maximizes throughput
- Robust error handling enables reliable operation
- Metadata separation from data reduces per-transfer overhead

