% Define Red Pitaya as TCP/IP object
close all
clc
IP = 'rp-f0a235.local';                % Input IP of your Red Pitaya...
port = 5000;
RP = tcpclient(IP, port);

dec = 1;
trig_lvl = 0;
gain = 'LV';
data_format = 'VOLTS';
data_units = 'RAW';
% coupling = 'AC';      % SIGNALlab 250-12 only
trig_dly = 0;
acq_trig = 'CH1_PE';

%% Open connection with your Red Pitaya
RP.ByteOrder = 'big-endian';
configureTerminator(RP,'CR/LF');
flush(RP);

% Acquire Data ASCII/VOLTS MODE
% Set decimation vale (sampling rate) in respect to the
% acquired signal frequency

writeline(RP,'ACQ:RST');
writeline(RP, append('ACQ:DEC:Factor ', num2str(dec)));
writeline(RP,append('ACQ:TRig:LEV ', num2str(trig_lvl)));

% Select acquisition units and format
writeline(RP, append('ACQ:SOUR1:GAIN ', gain));         % LV gain is selected by default
writeline(RP, append('ACQ:DATA:FORMAT ', data_format));    
writeline(RP, append('ACQ:DATA:Units ', data_units));        % BIN/VOLTS => VOLTS, BIN/RAW => RAW

% SIGNALlab 250-12 has an option to select input coupling
% writeline(RP, append('ACQ:SOUR1:COUP ', coupling));   % enables AC coupling on channel 1

% Set trigger delay to 0 samples
% 0 samples delay set trigger to center of the acquired data buffer
% The triggering moment is in the center (8192nd sample)
% Samples from left to the center were acquired before the trigger
% Samples from center to the right were acquired after the trigger

writeline(RP, append('ACQ:TRig:DLY ', num2str(trig_dly)));

%% Start & Trigger
% Trigger source command must be set after ACQ:START
% Set trigger to source 1 positive edge

writeline(RP,'ACQ:START');
% After acquisition is started, some time delay is needed in order to acquire fresh samples in to buffer
% Here we use a time delay of one second but you can calculate exact value taking in to account buffer
% length and sampling rate
pause(1)
writeline(RP, append('ACQ:TRig ', acq_trig));
% Wait for trigger
% Until trigger is true wait with acquiring
% Be aware of while loop if trigger is not achieved
% Ctrl+C will stop code executing in MATLAB

% % This loop can be skipped if waiting for buffer full condition
% while 1
%     trig_rsp = writeread(RP,'ACQ:TRig:STAT?')
%     if strcmp('TD', trig_rsp(1:2))  % Read only TD
%         break;
%     end
% end

% wait for fill adc buffer
while 1
    fill_state = writeread(RP,'ACQ:TRig:FILL?')
    if strcmp('1', fill_state(1:1))
        break;
    end
end

%%! Select one of the following codes depending on the units and format setting
%% ASCII VOLTS/RAW
% % Read data from buffer
% data_str = writeread(RP,'ACQ:SOUR1:DATA?');
% 
% % Convert values to numbers.
% % The first character in string is a "{" and the last character is a "}".
% 
% data = str2num(data_str(2:length(data_str)-1));
% 
% plot(data)
% grid on
% ylabel('Voltage / V')
% xlabel('Samples')
% 
% clear RP;

%% BIN VOLTS
% Read data from buffer
writeline(RP, 'ACQ:SOUR1:DATA?');
% Read header for binary format
header = read(RP, 1);

% Reading size of block, what informed about data size
header_size = str2double(strcat(read(RP, 1, 'int8')));

% Reading size of data (4*16384)
data_size = str2double(strcat(read(RP, header_size, 'char')));

% Read data
data = read(RP, data_size/4, 'single');       % BIN/VOLTS

plot(data)
grid on;
ylabel('Voltage / V')
xlabel('Samples')

clear RP;

%% BIN RAW
% % Read data from buffer
% writeline(RP, 'ACQ:SOUR1:DATA?');
% 
% % Read header for binary format
% header = read(RP, 1);
% 
% % Reading size of block, what informed about data size
% header_size = str2double(strcat(read(RP, 1, 'int8')));
%             
% % Reading size of data
% data_size =   str2double(strcat(read(RP, header_size, 'char'))')
%             
% % Read data
% data = read(RP, data_size/2, 'int16');      % BIN/RAW mode
%             
% plot(data)
% grid on;
% ylabel('Voltage / V')
% xlabel('Samples')
% 
% clear RP;
