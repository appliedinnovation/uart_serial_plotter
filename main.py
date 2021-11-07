#!/usr/bin/python
from main_window import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)
import sys


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("./images/icon.png"))
    MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
