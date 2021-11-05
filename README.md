# uart_serial_plotter

This project provides [pyqtgraph](https://www.pyqtgraph.org/) based applications for real-time plotting and analysis of timeseries data

## Features
- Fast, real-time plotting of time series data
- Plot timeseries data received over UART
- Plot timeseries data read from CSV file
- Dynamically change the serial port being monitored
- Export the plot / scane to PNG, SVG, CSV etc.
- Zoom into parts of the plot, reset the view, export/screenshot select portions of the plot

![image](https://i.imgur.com/vkrgcVm.png)

## Quick Start

The main program `main.py` allows for real-time plotting of CSV-formatted time series data received over UART / serial device.

```console
foo@bar:~$ python main.py -h
usage: main.py [-h] baudrate [header]

Plot CSV-formatted timeseries data received from UART

positional arguments:
  baudrate    UART baudrate
  header      Header for CSV-formatted timeseries data

options:
  -h, --help  show this help message and exit
```

The GUI allows the user to select the serial device (out of all the serial devices detected).

![image](https://i.imgur.com/KhoK05k.png)

![image](https://i.imgur.com/SqLQyEa.png)

![image](https://i.imgur.com/e6RhP3r.png)

## Loading CSV files

A second program, `main_csv.py`, can be used to read directly from CSV file instead of UART.

```console
foo@bar:~$ python main_csv.py -h
usage: main_csv.py [-h] csvfile

Plot CSV of timeseries data

positional arguments:
  csvfile     CSV file to parse

options:
  -h, --help  show this help message and exit
```
