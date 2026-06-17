%% Define Red Pitaya as TCP/IP object
IP= 'rp-f0a235.local';              % Input IP of your Red Pitaya...
port = 5000;
RP=tcpclient(IP, port);

%% Open connection with your Red Pitaya
RP.ByteOrder = 'big-endian';
configureTerminator(RP,'CR/LF');

writeline(RP,'DIG:RST');               % Reset digital pins and LED states
writeline(RP,'DIG:PIN:DIR IN,DIO5_N');  % Set DIO5_N  to be input
i=1;

while i<1000                            % You can set while 1 for continuous loop
    state = str2double(writeread(RP,'DIG:PIN? DIO5_N'));

    if state==0
        writeline(RP,'DIG:PIN LED5,1');
    else
        writeline(RP,'DIG:PIN LED5,0');
    end

    pause(0.1);                         % Set time delay for Red Pitaya response
    i=i+1;
end

%% Close connection with Red Pitaya
clear RP;
