close all;
clc;

%% Define Red Pitaya as TCP/IP object
IP = 'rp-f0a235.local';             % Input IP of your Red Pitaya...
port = 5000;
RP = tcpclient(IP, port);

%% Open connection with your Red Pitaya
RP.ByteOrder = 'big-endian';
configureTerminator(RP,'CR/LF');

%% Setup
a = 1;              % iteration
v0 = [];            % Voltage arrays
v1 = [];
v2 = [];
v3 = [];
f = gcf;            % Figure
hold on;

volts0 = str2double(writeread(RP,'ANALOG:PIN? AIN0'));
volts1 = str2double(writeread(RP,'ANALOG:PIN? AIN1'));
volts2 = str2double(writeread(RP,'ANALOG:PIN? AIN2'));
volts3 = str2double(writeread(RP,'ANALOG:PIN? AIN3'));

%% Plotting data
while (a < 500)
    v0(a) = str2double(writeread(RP,'ANALOG:PIN? AIN0'));
    v1(a) = str2double(writeread(RP,'ANALOG:PIN? AIN1'));
    v2(a) = str2double(writeread(RP,'ANALOG:PIN? AIN2'));
    v3(a) = str2double(writeread(RP,'ANALOG:PIN? AIN3'));
        
    % Plot 
    if (a < 150)
        plot(v0, 'LineWidth', 2, 'Color', [0 0.4470 0.7410]);
        plot(v1, 'LineWidth', 2, 'Color', [0.8500 0.3250 0.0980]);
        plot(v2, 'LineWidth', 2, 'Color', [0.9290 0.6940 0.1250]);
        plot(v3, 'LineWidth', 2, 'Color', [0.4660 0.6740 0.1880]);
    else
        clf;
        plot(v0(end-149:end), 'LineWidth', 2, 'Color', [0 0.4470 0.7410]);
        plot(v1(end-149:end), 'LineWidth', 2, 'Color', [0.8500 0.3250 0.0980]);
        plot(v2(end-149:end), 'LineWidth', 2, 'Color', [0.9290 0.6940 0.1250]);
        plot(v3(end-149:end), 'LineWidth', 2, 'Color', [0.4660 0.6740 0.1880]);
    end

    % Plot settings
    grid ON;
    xlabel('Samples');
    ylim([0 3.5]);
    ylabel('{\itU} [V]');
    title('Voltage');
    legend('v0','v1','v2','v3');
        
    pause(0.01);
    a = a+1;
end

%% Close connection with Red Pitaya
clear RP;
