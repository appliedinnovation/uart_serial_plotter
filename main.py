#!/usr/bin/python
import time
import glob
import sys
import os

import argparse
import csv

from multiprocessing import Process, Queue

from main_window import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore

import re

def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', str(line))

import signal
import serial

signal.signal(signal.SIGINT, signal.SIG_DFL)

parser = argparse.ArgumentParser(
    description="Plot CSV-formatted timeseries data received from UART"
)
parser.add_argument("baudrate", type=int, help="UART baudrate")
args = parser.parse_args()

serial_port = None
BAUD_RATE = args.baudrate

app = QApplication(sys.argv)


def on_port_changed_callback(port):
    global serial_port
    if serial_port:
        serial_port.close()
    serial_port = serial.Serial(port, BAUD_RATE)
    print("Listening on serial port", port)


window = MainWindow(on_port_changed_callback)
serial_port = serial.Serial(window.port, BAUD_RATE)


def main():
    def update():
        global header
        global serial_port
        global window

        try:
            if serial_port and serial_port.inWaiting() == 0:
                return  # do nothing
        except:
            return

        # read a line from serial port
        strdata = serial_port.readline()

        # and decode it
        if sys.version_info >= (3, 0):
            strdata = strdata.decode("utf-8", "backslashreplace")

        strdata = escape_ansi(strdata)
        arrdata = strdata.split(",")

        # return if there was not a comma
        if len(arrdata) < 5:
            return

        # determine if this line is a header or not (first value is string data)
        is_header = False
        try:
            dummy = float(arrdata[0])
        except ValueError:
            is_header = True

        if is_header:
            # an array of strings
            window.plot_page.plot.set_header(arrdata)
        else:
            # an array of numbers
            window.plot_page.plot.update_data([[float(x) for x in arrdata]])

    timer = QtCore.QTimer(timerType=0)  # Qt.PreciseTimer
    timer.timeout.connect(update)
    timer.start(20)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
