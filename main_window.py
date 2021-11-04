import glob
import sys
import serial
import serial.tools.list_ports
from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QComboBox,
    QApplication,
    QMainWindow,
    QStyleFactory,
    QDesktopWidget,
    QMessageBox,
    QErrorMessage,
    QFileDialog,
    QSplitter,
    QScrollArea,
)
from PyQt5.QtCore import (
    QFileInfo,
    QFile,
    QProcess,
    QTimer,
    QBasicTimer,
    Qt,
    QObject,
    QRunnable,
    QThread,
    QThreadPool,
    pyqtSignal,
)

from action import Action
import resource
import pages
from list_serial_ports import list_serial_ports


class MainWindow(QMainWindow):

    from menubar import menubar_init, menubar_add_menu, menu_add_action

    from toolbar import (
        toolbar_init,
        toolbar_create,
        toolbar_add_action,
        toolbar_add_widget,
        toolbar_add_separator,
        toolbar_remove,
    )

    def __init__(self):
        super().__init__()

        self.port = None
        self.__init_ui__()

    def __init_ui__(self):
        QApplication.setStyle(QStyleFactory.create("Cleanlooks"))

        self.setStyleSheet("QLabel {font: 15pt} QPushButton {font: 15pt}")
        self.setWindowTitle("UART Serial Plotter")

        # Create the actions for the program
        exitAction = Action(
            resource.path("icons/toolbar/exit.png"), "Exit Plotter", self
        )
        exitAction.setShortcut("Ctrl+Q")
        exitAction.setStatusTip("Exit application")
        exitAction.triggered.connect(self.close)

        refreshAction = Action(
            resource.path("icons/toolbar/refresh.png"), "Refresh Serial Ports", self
        )
        refreshAction.setShortcut("Ctrl+R")
        refreshAction.setStatusTip("Refresh Serial Port List")
        refreshAction.triggered.connect(self.refresh_ports)

        # Create the widgets for the program (embeddable in the
        # toolbar or elsewhere)
        self.port_selector = QComboBox(self)
        self.refresh_ports()
        self.port_selector.activated[str].connect(self.change_port)

        # Set up the Menus for the program
        self.menubar_init()
        self.menubar_add_menu("&File")
        self.menu_add_action("&File", exitAction)

        # Set up the toolbars for the program
        self.toolbar_init()
        self.toolbar_create("toolbar1")
        self.toolbar_add_action("toolbar1", exitAction)

        self.toolbar_add_separator("toolbar1")
        self.toolbar_add_action("toolbar1", refreshAction)
        self.toolbar_add_widget("toolbar1", QLabel(" Serial Port: "))
        self.toolbar_add_widget("toolbar1", self.port_selector)

        self.startPage = pages.StartPage()

        # main controls
        # self.setCentralWidget(self.pager)
        self.setGeometry(0, 0, 1200, 1000)
        self.center()
        self.show()

    def change_port(self, newPort):
        if newPort != self.port:
            self.port = newPort

    # Functions for serial port control
    def refresh_ports(self):
        self.serial_ports = list_serial_ports()
        self.port_selector.clear()
        self.port_selector.addItems(self.serial_ports)
        if self.port is None and len(self.serial_ports):
            self.port = self.serial_ports[0]
        if self.port is not None and len(self.serial_ports):
            self.port_selector.setCurrentIndex(self.serial_ports.index(self.port))
        else:
            self.port_selector.setCurrentIndex(-1)

    # window functions
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def close_event(self, event):
        reply = QMessageBox.question(
            self,
            "Quit",
            "Sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.stop()
            event.accept()
        else:
            event.ignore()
