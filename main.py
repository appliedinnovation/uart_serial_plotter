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


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
