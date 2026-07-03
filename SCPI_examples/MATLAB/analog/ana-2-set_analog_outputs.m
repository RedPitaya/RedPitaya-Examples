%% Define Red Pitaya as TCP/IP object
IP = 'rp-f0a235.local';         % Input IP of your Red Pitaya...
port = 5000;
RP = tcpclient(IP, port);

%% Open connection with your Red Pitaya
RP.ByteOrder = 'big-endian';
configureTerminator(RP,'CR/LF');

writeline(RP,'ANALOG:PIN AOUT0,0.3');  % 0.3 Volts is set on output 0
writeline(RP,'ANALOG:PIN AOUT1,0.9');
writeline(RP,'ANALOG:PIN AOUT2,1.0');
writeline(RP,'ANALOG:PIN AOUT3,1.5');

clear RP;
