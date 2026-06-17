%% Define Red Pitaya as TCP/IP object
IP  = 'rp-f0a235.local';        % Input IP of your Red Pitaya...
port = 5000;
RP = tcpclient(IP, port);

%% Open connection with your Red Pitaya

RP.ByteOrder = "big-endian";
configureTerminator(RP,'CR/LF');
%% Define value p from 0 - 100 %
p = 85;    % Set value of p

if p >=(100/9)
     writeline(RP,'DIG:PIN LED0,1')
 else
     writeline(RP,'DIG:PIN LED0,0')
 end

if p >=(100/9)*2
    writeline(RP,'DIG:PIN LED1,1')
else
    writeline(RP,'DIG:PIN LED1,0')
end

if p >=(100/9)*3
    writeline(RP,'DIG:PIN LED2,1')
else
    writeline(RP,'DIG:PIN LED2,0')
end

if p >=(100/9)*4
    writeline(RP,'DIG:PIN LED3,1')
else
    writeline(RP,'DIG:PIN LED3,0')
end

if p >=(100/9)*5
    writeline(RP,'DIG:PIN LED4,1')
else
    writeline(RP,'DIG:PIN LED4,0')
end

if p >=(100/9)*6
    writeline(RP,'DIG:PIN LED5,1')
else
    writeline(RP,'DIG:PIN LED5,0')
end

if p >=(100/9)*7
    writeline(RP,'DIG:PIN LED6,1')
else
    writeline(RP,'DIG:PIN LED6,0')
end

if p >=(100/9)*8
    writeline(RP,'DIG:PIN LED7,1')
else
    writeline(RP,'DIG:PIN LED7,0')
end

clear RP;
