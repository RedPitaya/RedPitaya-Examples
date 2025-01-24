/* @brief This is a simple application for testing UART communication on a RedPitaya
*
* (c) Red Pitaya  http://www.redpitaya.com
*
* This part of code is written in C programming language.
* Please visit http://en.wikipedia.org/wiki/C_(programming_language)
* for more details on the language used herein.
*/

#include <chrono>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>                 //Used for UART
#include <fcntl.h>                  //Used for UART
#include <termios.h>                //Used for UART
#include <errno.h>
#include <stdint.h>

#define B_SIZE 40

class UARTProtocol{

public:
    auto writeTo(int fd, uint8_t *buffer, size_t size) -> size_t;
    auto readFrom(int fd, uint8_t *buffer, size_t size) -> size_t;
    auto setTimeout(uint32_t timeout) -> void {m_timeout = timeout;};
private:
    auto readBlock(int fd, uint8_t *buffer, size_t size, bool first) -> size_t;
    auto getHeaderForBlock(uint8_t *buffer, uint8_t size, bool firstBlock) -> uint8_t;
    auto uart_read(int fd, unsigned char *_buffer, uint8_t size) -> int;
    auto uart_write(int fd, unsigned char *_buffer, uint8_t size) -> int;
    static auto crc4(uint8_t *data, uint8_t size) -> uint8_t;

    uint32_t m_timeout = 0;
};

auto UARTProtocol::crc4(uint8_t *data, uint8_t size) -> uint8_t{
	const uint8_t CRC4_POLY = 0x13;
	uint8_t crc = 0;
	for (uint8_t z = 0; z < size; z++) {
		uint8_t byte = data[z];
		for (int i = 7; i >= 0; --i) {
			bool bit = (byte >> i) & 1;
			bool crc_msb = crc & 0x08;
			crc <<= 1;
			if (crc_msb ^ bit) {
				crc ^= CRC4_POLY;
			}
			crc &= 0x0F;
		}
	}
	return crc;
}

auto UARTProtocol::uart_read(int fd, unsigned char *_buffer, uint8_t size) -> int{
    auto current = std::chrono::system_clock::now();
    while (1){
        if (fd == -1){
            printf("Failed to read from UART. UART is closed.\n");
            return -1;
        }

        errno = 0;
        int rx_length = read(fd, (void *)_buffer, size);
        if (rx_length < 0){
            /* No data yet avaliable, check again */
            if (errno == EAGAIN){
                auto diff = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now() - current);
                if (diff.count() > m_timeout && m_timeout != 0){
                    return -1;
                }

                continue;
                /* Error differs */
            }
            else{
                printf("Error read from UART. Errno: %d\n", errno);
                return -1;
            }
        }
        else{
            return rx_length;
        }
    }
    return 0;
}

auto UARTProtocol::uart_write(int fd, unsigned char *_buffer, uint8_t size) -> int{
    int count = 0;
    if (fd != -1){
        count = write(fd, _buffer, size);
    }
    else{
        printf("Failed write to UART.\n");
        return -1;
    }

    if (count < 0){
        printf("Failed write to UART.\n");
        return -1;
    }

    return count;
}

auto UARTProtocol::readFrom(int fd, uint8_t *buffer, size_t size) -> size_t{
    size_t pos = 0;
    uint8_t receiveSize = size < 8 ? size : 8;
    bool first = true;
    while(pos < size){
        uint8_t ret = readBlock(fd, buffer + pos, receiveSize, first);
        if (ret != receiveSize){
            return 0;
        }
        first = false;
        pos += ret;
        receiveSize = size - pos > 8 ? 8 : size - pos;
    }
    return pos;
}

auto UARTProtocol::readBlock(int fd, uint8_t *buffer, size_t size, bool first) -> size_t{
    uint8_t header = 0;
    uint8_t ret = uart_read(fd, &header, 1);
    if (ret != 1){
        fprintf(stderr, "Error reading header\n");
        return 0;
    }
    uint8_t readSize = (header & 0x07) + 1;
    if (first != (bool)(header & 0x8)){
        tcflush(fd, TCIFLUSH);
        fprintf(stderr,"Error block order 0x%X order %d\n", header, first);
        return 0;
    }
    if (readSize > size){
        fprintf(stderr,"Block size %d is larger than buffer size %d\n", readSize, size);
        return 0;
    }
    ret = uart_read(fd, buffer, readSize);
    if (ret != readSize){
        fprintf(stderr,"Buffer read error. Read size %d\n", ret);
        return 0;
    }
    uint8_t headerReceive = getHeaderForBlock(buffer, readSize, first);
    if (headerReceive != header){
        fprintf(stderr,"The receive does not match the packet header 0x%X != 0x%X\n", header, headerReceive);
        return 0;
    }
    ret = uart_write(fd, &headerReceive, 1);
    if (ret != 1){
        return 0;
    }
    return readSize;
}

auto UARTProtocol::writeTo(int fd, uint8_t *buffer, size_t size) -> size_t{
    size_t pos = 0;
    uint8_t sendSize = size < 8 ? size : 8;
    bool first = true;
    while(pos < size){
        uint8_t header = getHeaderForBlock(buffer + pos, sendSize, first);
        uint8_t ret = uart_write(fd, &header, 1); // Send header at first
        if (ret != 1){
            return pos;
        }
        first = false;
        ret = uart_write(fd,buffer + pos, sendSize);  // Send data block
        if (ret != sendSize){
            return pos + ret;
        }
        uint8_t headerResponse = 0;
        ret = uart_read(fd, &headerResponse, 1);
        if (headerResponse != header){
            fprintf(stderr,"The response does not match the packet header 0x%X != 0x%X\n",header, headerResponse);
            return pos;
        }
        pos += sendSize;
        sendSize = pos + sendSize < size ? sendSize : size - pos;
    }
    return 0;
}

auto UARTProtocol::getHeaderForBlock(uint8_t *buffer, uint8_t size, bool firstBlock) -> uint8_t{
    if (size == 0){
        fprintf(stderr,"Buffer size cannot be 0\n");
        return 0;
    }
    if (size > 8){
        fprintf(stderr,"The size %d is larger than the allowed 8\n",size);
        return 0;
    }
    uint8_t value = crc4(buffer, size);
	value = value << 4;
    value = (value & 0xF0) | ((size - 1) & 0x07) | (firstBlock ? 0x8 : 0);
    return value;
}


/* Inline function definition */
static int uart_init();
static int release();

/* File descriptor definition */
int uart_fd = -1;

static int uart_init(){

    uart_fd = open("/dev/ttyPS1", O_RDWR | O_NOCTTY | O_NDELAY);

    if(uart_fd == -1){
        fprintf(stderr, "Failed to open uart.\n");
        return -1;
    }

    struct termios settings;
    tcgetattr(uart_fd, &settings);

    /*  CONFIGURE THE UART
    *  The flags (defined in /usr/include/termios.h - see http://pubs.opengroup.org/onlinepubs/007908799/xsh/termios.h.html):
    *       Baud rate:- B1200, B2400, B4800, B9600, B19200, B38400, B57600, B115200, B230400, B460800, B500000, B576000, B921600, B1000000, B1152000, B1500000, B2000000, B2500000, B3000000, B3500000, B4000000
    *       CSIZE:- CS5, CS6, CS7, CS8
    *       CLOCAL - Ignore modem status lines
    *       CREAD - Enable receiver
    *       IGNPAR = Ignore characters with parity errors
    *       ICRNL - Map CR to NL on input (Use for ASCII comms where you want to auto correct end of line characters - don't use for bianry comms!)
    *       PARENB - Parity enable
    *       PARODD - Odd parity (else even) */

    /* Set baud rate - default set to 9600Hz */
    speed_t baud_rate = B9600;

    /* Baud rate fuctions
    * cfsetospeed - Set output speed
    * cfsetispeed - Set input speed
    * cfsetspeed  - Set both output and input speed */

    cfsetspeed(&settings, baud_rate);

    settings.c_cflag &= ~CSIZE;
    settings.c_cflag |= CS8 | CLOCAL | CREAD; /* 8 bits */
    settings.c_cflag &= ~CRTSCTS; // Disable flow control
    settings.c_iflag &= ~(IXON | IXOFF | IXANY);          // Disable XON/XOFF flow control both input & output
    settings.c_iflag &= ~(ICANON | ECHO | ECHOE | ISIG);  // Non Cannonical mode
    settings.c_iflag &= ~ICRNL;
    settings.c_oflag &= ~OPOST; /* raw output */

    settings.c_lflag = 0;               //  enable raw input instead of canonical,
    settings.c_cc[VMIN]  = 1;           // Read at least 1 character
    settings.c_cc[VTIME]  = 0;

    /* Setting attributes */
    tcflush(uart_fd, TCIFLUSH);
    tcsetattr(uart_fd, TCSANOW, &settings);

    return 0;
}


static int release(){

    tcflush(uart_fd, TCIFLUSH);
    close(uart_fd);

    return 0;
}

int main(int argc, char *argv[]){

    uint8_t buffer[B_SIZE];
    for(int i = 0 ; i < B_SIZE; i++){
        buffer[i] = i;
    }

    /* uart init */
    if(uart_init() < 0){
        printf("Uart init error.\n");
        return -1;
    }
    UARTProtocol p;
    p.setTimeout(5000);

    while(1){

        memset(buffer,0,B_SIZE);
        printf("Begin read\n");
        auto ret = p.readFrom(uart_fd,buffer,B_SIZE);
        if (ret == B_SIZE){
            printf("End read\n");
            for(int i = 0 ; i < B_SIZE; i++){
                printf("%d,",buffer[i]);
            }
            printf("\n");
            for(int i = 0 ; i < B_SIZE; i++){
                buffer[i] = i * 2;
            }
            printf("Begin write\n");
            p.writeTo(uart_fd,buffer,B_SIZE);
            printf("End write\n");
        }else{
            printf("Error read\n");
        }
        sleep(2);
    }

    /* CLOSING UART */
    release();

    return 0;
}
