function RedPitaya_sliderAnalogDemo

    fig = uifigure("Position", [100 100 300 250]);      % Create figure
    p = 0;

    sld = uislider( ...                               % Create slider
        Parent= fig,...                               % Parent figure
        Value= 10,...                                 % Default value
        Limits= [0 100],...                           % Slider limits
        Orientation= 'horizontal',...                 % Orientation
        ValueChangingFcn= @(src, event)sliderCallback(src, event, p));
        
    function  sliderCallback(src, event, p)
        p = event.Value;

        %% Define Red Pitaya as TCP/IP object
        IP = 'rp-f0a235.local';         % Input IP of your Red Pitaya...
        port = 5000;
        RP = tcpclient(IP, port);

        %% Open connection with your Red Pitaya
        RP.ByteOrder = 'big-endian';
        configureTerminator(RP,'CR/LF');

        %% Set your output voltage value and pin
        out_voltage = num2str((1.8/100)*p);     % From 0 - 1.8 volts
        out_num = '2';                          % Analog outputs 0,1,2,3
            
        %% Set your SCPI command with strcat function
        scpi_command = strcat('ANALOG:PIN AOUT',out_num,',',out_voltage);

        %% Send SCPI command to Red Pitaya
        writeline(RP, scpi_command);

        %% Close connection with Red Pitaya
        clear RP;
    end
end
