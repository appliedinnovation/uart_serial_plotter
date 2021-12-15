# uart_serial_plotter

This project provides [pyqtgraph](https://www.pyqtgraph.org/) based applications for real-time plotting and analysis of timeseries data

## Features
- Fast, real-time plotting of time series data
- Plot timeseries data received over UART
- Plot timeseries data read from CSV file
- Dynamically change the serial port being monitored
- Detect new USB devices connected to system and automatically update available serial ports
  - Currently only implemented for Windows
- Export the plot / scane to PNG, SVG, CSV etc.
- Load previously exported CSV files of plot / scene
- Zoom into parts of the plot, reset the view, export/screenshot select portions of the plot
- Reset the connected device using DTR/RTS hardware flow control
  - Tested on ESP32

## Quick Start

```console
foo@bar:~$ python src/main.py
```


## Notes:

* For M1 Macs, you can either run the MacOS release or, if you are developing / would like to run source, you may need to follow the instructions here to use a python environment within rosetta: https://stackoverflow.com/questions/65901162/how-can-i-run-pyqt5-on-my-mac-with-m1chip
