import functools
from numpy import empty
from pyqtgraph.graphicsItems.ScatterPlotItem import ScatterPlotItem
import serial
import serial.tools.list_ports
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QActionGroup,
    QMenu,
    QSizePolicy,
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
    QDialog,
    QFileDialog,
    QSplitter,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QStatusBar,
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

from pyqtgraph.GraphicsScene import exportDialog

from action import Action
import resource
import pages
from list_serial_ports import list_serial_ports
from pager import Pager
import csv


class MainWindow(QMainWindow):

    from menubar import (
        menubar_init,
        menubar_add_menu,
        menubar_get_menu,
        menu_add_action,
    )

    def __init__(
        self,
        on_port_changed_callback=None,
        on_baudrate_changed_callback=None,
        on_reset_device_callback=None,
    ):
        super().__init__()

        self.port = None
        self.baudrate = 115200
        self.baudrate_values = [
            110,
            150,
            300,
            1200,
            2400,
            4800,
            9600,
            19200,
            38400,
            57600,
            115200,
            230400,
            460800,
            921600,
        ]

        self.on_port_changed_callback = on_port_changed_callback
        self.on_baudrate_changed_callback = on_baudrate_changed_callback
        self.on_reset_device_callback = on_reset_device_callback
        self.__init_ui__()

    def __init_ui__(self):
        QApplication.setStyle(QStyleFactory.create("Cleanlooks"))

        self.setStyleSheet("QLabel {font: 15pt} QPushButton {font: 15pt}")
        self.setWindowTitle("UART Serial Plotter")

        self.__init_actions__()
        self.__init_menubar__()

        self.setStyleSheet("QMainWindow { background-color: rgb(0,0,0); }")

        self.plot_page = pages.PlotPage()
        self.plot_page.plot.plot_item.clear()

        self.text_edit = QTextEdit()
        font = QtGui.QFont("Monospace")
        font.setStyleHint(QtGui.QFont.Monospace)
        font.setPointSize(11)
        self.text_edit.setFont(font)
        self.text_edit.verticalScrollBar().setStyleSheet(
            "QScrollBar { background-color: rgb(42,42,42); }"
        )
        self.text_edit.setStyleSheet(
            "QTextEdit { background-color: rgb(12,12,12); color: rgb(255, 255, 255); padding-left: 20px; }"
        )

        # self.statusBar = QStatusBar()
        # self.statusBar.setFont(font)
        # self.statusBar.setStyleSheet("QStatusBar { text-align: right; background-color: rgb(12,12,12); padding-left: 20px; }")

        splitter = QSplitter(QtCore.Qt.Vertical)
        layout = QVBoxLayout()
        splitter.setStyleSheet("QWidget { background-color: rgb(42, 42, 42); }")
        splitter.addWidget(self.plot_page)
        splitter.addWidget(self.text_edit)
        # splitter.addWidget(self.statusBar)
        layout.addWidget(splitter)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.center()
        self.showMaximized()

    def __init_actions__(self):
        self.exitAction = Action(None, "Exit", self)
        self.exitAction.setStatusTip("Exit")
        self.exitAction.setShortcut("Ctrl+Q")
        self.exitAction.triggered.connect(self.close)

        self.refreshAction = Action(None, "Refresh", self)
        self.refreshAction.setStatusTip("Refresh Serial Ports")
        self.refreshAction.triggered.connect(self.__refresh_ports__)

        self.resetDevice = Action(None, "Reset Device", self)
        self.resetDevice.setStatusTip("Reset Device")
        self.resetDevice.triggered.connect(self.__reset_device__)

        self.rescaleAxesAction = Action(None, "Rescale Axes", self)
        self.rescaleAxesAction.setShortcut("Ctrl+R")
        self.rescaleAxesAction.triggered.connect(self.__rescale_axes__)

        self.clearPlotAction = Action(None, "Clear Plot", self)
        self.clearPlotAction.triggered.connect(self.__clear_plot__)

        self.importSceneAction = Action(None, "Import from CSV", self)
        self.importSceneAction.setShortcut("Ctrl+O")
        self.importSceneAction.setStatusTip("Import scene")
        self.importSceneAction.triggered.connect(self.__import_scene__)

        self.exportSceneAction = Action(None, "Export...", self)
        self.exportSceneAction.setShortcut("Ctrl+S")
        self.exportSceneAction.setStatusTip("Export scene")
        self.exportSceneAction.triggered.connect(self.__export_scene__)

    def __init_menubar__(self):
        self.menubar_init()
        self.menubar_add_menu("&File")
        self.menu_add_action("&File", self.importSceneAction)
        self.menu_add_action("&File", self.exportSceneAction)
        self.menu_add_action("&File", self.exitAction)

        self.menubar_add_menu("&View")
        self.menu_add_action("&View", self.rescaleAxesAction)
        self.menu_add_action("&View", self.clearPlotAction)

        self.menubar_add_menu("&Serial")
        self.__refresh_ports__()

    def __init_port_menu__(self):
        serial_menu = self.menubar_get_menu("&Serial")
        serial_menu.clear()
        self.menu_add_action("&Serial", self.refreshAction)
        ports_submenu = serial_menu.addMenu("&Port")

        # Serial ports submenu
        if len(self.serial_ports):
            self.ports_action_group = QActionGroup(self)
            for i in range(len(self.serial_ports)):
                port_name = self.serial_ports[i]
                action = ports_submenu.addAction(
                    "&" + str(port_name),
                    functools.partial(self.__on_port_changed__, port_name),
                )
                action.setCheckable(True)
                # Check the last serial port
                if i == len(self.serial_ports) - 1:
                    action.setChecked(True)
                    self.port = self.serial_ports[i]
                    if self.on_port_changed_callback:
                        self.on_port_changed_callback(self.port)
                self.ports_action_group.addAction(action)
            self.ports_action_group.setExclusive(True)
        else:
            ports_submenu.setEnabled(False)

        self.__init_baudrate_menu__()
        self.menu_add_action("&Serial", self.resetDevice)
        if len(self.serial_ports) == 0:
            self.resetDevice.setEnabled(False)

    def __init_baudrate_menu__(self):
        serial_menu = self.menubar_get_menu("&Serial")
        baudrate_submenu = serial_menu.addMenu("&Baud Rate")

        self.baudrate_action_group = QActionGroup(self)
        for baud in self.baudrate_values:
            action = baudrate_submenu.addAction(
                "&" + str(baud), functools.partial(self.__on_baudrate_changed__, baud)
            )
            action.setCheckable(True)
            if baud == self.baudrate:
                action.setChecked(True)
            self.baudrate_action_group.addAction(action)
        self.baudrate_action_group.setExclusive(True)

    def __on_port_changed__(self, newPort):
        if newPort != self.port:
            self.port = newPort
        self.on_port_changed_callback(self.port)

    def __on_baudrate_changed__(self, newBaudRate):
        print(newBaudRate)
        if newBaudRate != self.baudrate:
            self.baudrate = newBaudRate
        self.on_baudrate_changed_callback(int(self.baudrate))

    def __refresh_ports__(self):
        self.serial_ports = list_serial_ports()
        self.__init_port_menu__()
        if len(self.serial_ports) == 0:
            self.resetDevice.setEnabled(False)
        else:
            self.resetDevice.setEnabled(True)

    def __reset_device__(self):
        if self.on_reset_device_callback:
            self.on_reset_device_callback()

    def __rescale_axes__(self):
        self.plot_page.plot.canvas.getPlotItem().disableAutoRange()
        self.plot_page.plot.canvas.getPlotItem().enableAutoRange()

    def __clear_plot__(self):
        self.plot_page.plot.plot_item.clear()
        self.plot_page.plot.traces = {}
        self.plot_page.plot.trace_names = []
        self.plot_page.plot.data = {}

    def __export_scene__(self):
        try:
            e = exportDialog.ExportDialog(self.plot_page.plot.canvas.plotItem.scene())
            e.show(self.plot_page.plot.canvas.plotItem)
        except:
            pass

    def __import_scene__(self):
        dialog = QFileDialog()
        fmt = "csv"
        dialog.setDefaultSuffix(fmt)
        dialog.setNameFilters([f"{fmt} (*.{fmt})"])

        if dialog.exec_() == QDialog.Accepted:
            path = dialog.selectedFiles()[0]
            with open(path, "r") as csvfile:
                reader = csv.reader(csvfile)

                # Parse Header
                # Expected: "Foo_x","Foo_y","Bar_x","Bar_y",...
                # Convert to: "Foo","Bar",...
                header = ["_".join(h.strip().split("_")[:-1]) for h in next(reader)]
                header = list(dict.fromkeys(header))
                header.insert(0, "Time")

                # Clear existing plot and set new header
                self.__clear_plot__()
                self.plot_page.plot.set_header(header)

                dataset = []
                for row in reader:
                    time = float(row[0])
                    signals = [float(x) for x in row[1::2]]
                    data = []
                    data.append(time)
                    data.extend(signals)
                    dataset.append(data)
                self.plot_page.plot.update_data(dataset)

    # window functions
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
