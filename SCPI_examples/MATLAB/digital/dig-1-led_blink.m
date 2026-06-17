%% Define Red Pitaya as TCP/IP object

IP = ('rp-f0a235.local');               % Input IP of your Red Pitaya...
port = 5000;
RP = tcpclient(IP, port);               % creates a TCP client object
    
%% Open connection with your Red Pitaya
RP.ByteOrder = "big-endian";
configureTerminator(RP, 'CR/LF');       % defines the line terminator (end sequence of input characters)
    
%% Send SCPI command to Red Pitaya to turn ON LED1
for i=1:5
    writeline(RP,'DIG:PIN LED1,1');     % Peripheral_Unit: Unit_Part/function:subfunction/settings 
    % readline()                        % reading data
    % writeread()                       % send a command and read the reply
    
    pause(1);                           % Set time of LED ON
    
    % Send SCPI command to Red Pitaya to turn OFF LED1
    writeline(RP,'DIG:PIN LED1,0');
    
    % other possible commands:
    % DIG:PIN:DIR <dir>,<gpio>
    % DIG:PIN <pin>,<state>
    % DIG:PIN? <pin> => <state>         % Acquire status or read data
    
    pause(1);
end
%% Close connection with Red Pitaya
    
clear RP;
