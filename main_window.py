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
from pager import Pager


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

    def __init__(self, on_port_changed_callback=None):
        super().__init__()

        self.port = None
        self.__init_ui__()
        self.on_port_changed_callback = on_port_changed_callback

    def __init_ui__(self):
        QApplication.setStyle(QStyleFactory.create("Cleanlooks"))

        self.setStyleSheet("QLabel {font: 15pt} QPushButton {font: 15pt}")
        self.setWindowTitle("UART Serial Plotter")

        self.__init_actions__()
        self.__init_port_selector_combo_box__()
        self.__init_menubar__()
        self.__init_toolbar__()

        self.plot_page = pages.PlotPage()

        # main controls
        self.setCentralWidget(self.plot_page)
        self.setGeometry(0, 0, 1200, 1000)
        self.center()
        self.show()

    def __init_actions__(self):
        self.exitAction = Action(
            resource.path("icons/toolbar/exit.png"), "Exit Plotter", self
        )
        self.exitAction.setShortcut("Ctrl+Q")
        self.exitAction.setStatusTip("Exit application")
        self.exitAction.triggered.connect(self.close)

        self.refreshAction = Action(
            resource.path("icons/toolbar/refresh.png"), "Refresh Serial Ports", self
        )
        self.refreshAction.setShortcut("Ctrl+R")
        self.refreshAction.setStatusTip("Refresh Serial Port List")
        self.refreshAction.triggered.connect(self.__refresh_ports__)

        self.resetViewAction = Action(
            resource.path("icons/toolbar/reset.png"), "Reset View", self
        )
        self.resetViewAction.setShortcut("Ctrl+]")
        self.resetViewAction.setStatusTip("Reset View")
        self.resetViewAction.triggered.connect(self.__reset_view__)

    def __init_menubar__(self):
        self.menubar_init()
        self.menubar_add_menu("&File")
        self.menu_add_action("&File", self.exitAction)
        self.menu_add_action("&File", self.refreshAction)

    def __init_port_selector_combo_box__(self):
        self.port_selector = QComboBox(self)
        self.__refresh_ports__()
        self.port_selector.activated[str].connect(self.__on_port_changed__)

    def __init_toolbar__(self):
        self.toolbar_init()
        self.toolbar_create("toolbar1")
        self.toolbar_add_action("toolbar1", self.exitAction)

        self.toolbar_add_separator("toolbar1")
        self.toolbar_add_action("toolbar1", self.refreshAction)
        self.toolbar_add_widget("toolbar1", QLabel(" Serial Port: "))
        self.toolbar_add_widget("toolbar1", self.port_selector)
        self.toolbar_add_separator("toolbar1")
        self.toolbar_add_action("toolbar1", self.refreshAction)
        self.toolbar_add_action("toolbar1", self.resetViewAction)

    def __on_port_changed__(self, newPort):
        if newPort != self.port:
            self.port = newPort
            self.on_port_changed_callback(self.port)

    def __refresh_ports__(self):
        self.serial_ports = list_serial_ports()
        self.port_selector.clear()
        self.port_selector.addItems(self.serial_ports)
        if self.port is None and len(self.serial_ports):
            self.port = self.serial_ports[-1]
        if self.port is not None and len(self.serial_ports):
            self.port_selector.setCurrentIndex(self.serial_ports.index(self.port))
        else:
            self.port_selector.setCurrentIndex(-1)

    def __reset_view__(self):
        self.plot_page.plot.canvas.getPlotItem().enableAutoRange()

    # window functions
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
