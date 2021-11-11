#!/usr/bin/python
from main_window import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)
import sys

from resource_helpers import path

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(path("images/icon.png")))
    MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
