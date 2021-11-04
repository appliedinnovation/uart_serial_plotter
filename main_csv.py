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

import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)


parser = argparse.ArgumentParser(description='Plot CSV of timeseries data')
parser.add_argument('csvfile', help='CSV file to parse')
args = parser.parse_args()

app = QApplication(sys.argv)
window = MainWindow()

# Open CSV file
csvfile = open(args.csvfile, 'r')
reader = csv.reader(csvfile)

def main():
    header = next(reader)
    window.plot_page.plot.set_header(header)

    def update():
        global reader
        global window
        window.plot_page.plot.update_data([[float(x) for x in row] for row in reader])

    update()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()