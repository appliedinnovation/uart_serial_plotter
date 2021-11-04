#!/usr/bin/python
import time
import glob
import sys
import os

import argparse

# for spawning lpc21isp process
from multiprocessing import Process, Queue

from main_window import MainWindow
from PyQt5.QtWidgets import QApplication

import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    window.plot_page.plot.set_header(
        [
            "Time",
            "Velocity_setpoint",
            "Duty Cycle",
            "Velocity_current",
            "Acceleration_current",
        ]
    )
    window.plot_page.plot.update_data([[0.325, 600, 12, 349, 0.56]])
    window.plot_page.plot.update_data([[0.345, 600, 15, 398, 0.55]])
    window.plot_page.plot.update_data([[0.365, 600, 18, 403, 0.54]])
    window.plot_page.plot.update_data([[0.385, 600, 23, 421, 0.53]])

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
