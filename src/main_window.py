import functools
import os
from PyQt5 import QtWidgets
import re
import serial
import serial.tools.list_ports

import sys

from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QActionGroup,
    QWidget,
    QApplication,
    QMainWindow,
    QStyleFactory,
    QDesktopWidget,
    QDialog,
    QFileDialog,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
)

from action import Action
from pages import PlotPage
from list_serial_ports import list_serial_ports, list_serial_ports_by_descriptors
import csv
from tabs import Tabs


class MainWindow(QMainWindow):

    from menubar import (
        menubar_init,
        menubar_add_menu,
        menubar_get_menu,
        menu_add_action,
    )

    def __init__(self):
        super().__init__()

        # for force gauge
        self.force_gauge_serial_port = None
        self.force_gauge_port = None
        self.force_gauge_baudrate = 115200
        self.force_gauge_header = 'Force (lbf)'
        self.force_gauge_value = 0

        # for the normal data stream
        self.serial_port = None
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

        self.__init_ui__()

        # At this point, the menubar is initialized
        # which would've called __refresh_ports__()
        #
        # If there is a port, open it
        if self.port:
            self.log("Current port: " + str(self.port))
            self.__reopen_serial_port__()
            self.__change_menubar_text_open_close_port__()
        else:
            self.log("No device connected")

        self.update_timer = QtCore.QTimer(timerType=0)  # Qt.PreciseTimer
        self.update_timer.timeout.connect(self.__update_plot__)

        PLOT_UPDATE_FREQUENCY_HZ = 60
        PLOT_UPDATE_PERIOD_MS = int(float(1.0 / PLOT_UPDATE_FREQUENCY_HZ) * 1000)
        self.update_timer.start(PLOT_UPDATE_PERIOD_MS)

    def __init_font__(self):
        fontDatabase = QtGui.QFontDatabase()
        families = fontDatabase.families()

        desired_font = "Consolas"
        self.font = None
        if desired_font in families:
            self.font = QtGui.QFont(desired_font)
        else:
            self.font = QtGui.QFont("Monospace")
        self.font.setStyleHint(QtGui.QFont.System)
        self.font.setPointSize(10)

    def __get_editor_stylesheet__(self):
        return """
        QTextEdit {
            background: rgb(27,27,28); border-color: gray; color: rgb(255, 255, 255);
        }
        QScrollBar {
            background: rgb(74,73,73); height: 0px; width: 0px; 
        }
        QScrollBar::handle:vertical {
            background: rgb(74,73,73);
        }
        QScrollBar::add-line:vertical {
            border: none;
            background: rgb(74,73,73);
        }
        QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }"""

    def __init_ui__(self):
        QApplication.setStyle(QStyleFactory.create("Cleanlooks"))
        self.__init_font__()
        self.log_editor = QTextEdit()
        self.log_editor.setFont(self.font)
        self.log_editor.setStyleSheet(self.__get_editor_stylesheet__())

        self.setWindowTitle("UART Serial Plotter")

        # Initialize the plot
        self.plot_page = PlotPage()
        self.plot_page.plot.plot_item.clear()
        self.plot_page.plot.canvas.getAxis("left").tickFont = self.font
        self.plot_page.plot.canvas.getAxis("bottom").tickFont = self.font

        self.plot_tab = Tabs(self)
        self.plot_tab.addTab(
            self.plot_page, str(self.port) if self.port is not None else "Untitled"
        )
        self.plot_tab.setTabText(0, str(self.port) if self.port is not None else "No Port / File Selected")
        self.plot_tab.setStyleSheet(
            "QTabBar::tab:selected {font-weight: bold}"
            "QTabBar::tab {background: rgb(27,27,28); color: white;}"
            "QTabWidget:pane {border: 1px solid gray;}"
        )
        self.plot_tab.setFont(self.font)

        self.__init_actions__()
        self.__init_menubar__()

        self.setStyleSheet("QMainWindow { background-color: rgb(27,27,28); }")

        self.output_editor = QTextEdit()
        self.output_editor.setFont(self.font)
        self.output_editor.setStyleSheet(self.__get_editor_stylesheet__())

        self.tabs = Tabs(self)
        self.tabs.addTab(self.output_editor, "Output")
        self.tabs.setTabText(0, "Output")
        self.tabs.addTab(self.log_editor, "Log")
        self.tabs.setTabText(1, "Log")
        self.tabs.setStyleSheet(
            "QTabBar::tab:selected {font-weight: bold}"
            "QTabBar::tab {background: rgb(27,27,28); color: white;}"
            "QTabWidget:pane {border: 1px solid gray;}"
        )
        self.tabs.setFont(self.font)

        splitter = QSplitter(QtCore.Qt.Vertical)
        layout = QVBoxLayout()
        splitter.setStyleSheet("QWidget {background: rgb(27, 27, 28);}")
        splitter.addWidget(self.plot_tab)
        splitter.addWidget(self.tabs)
        layout.addWidget(splitter)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.__center_window__()
        self.showMaximized()

    def __init_actions__(self):
        self.exitAction = Action(None, "Exit", self)
        self.exitAction.setStatusTip("Exit")
        self.exitAction.setShortcut("Ctrl+Q")
        self.exitAction.triggered.connect(self.close)

        self.exportOutputWindowAction = Action(None, "Export UART data", self)
        self.exportOutputWindowAction.setStatusTip(
            "Exports all the data received so far to a .txt file"
        )
        self.exportOutputWindowAction.triggered.connect(
            self.__save_received_data_to_file__
        )

        self.autoClearPlotAction = Action(None, "Clear Plot on Reset", self)
        self.autoClearPlotAction.setStatusTip(
            "Clears the plot when a new header is received/detected"
        )
        self.autoClearPlotAction.triggered.connect(self.__on_auto_clear_plot_action__)
        self.autoClearPlotAction.setCheckable(True)
        self.autoClearPlotAction.setChecked(False)
        self.auto_clear_plot_on_header_change = False

        self.refreshAction = Action(None, "Refresh Ports", self)
        self.refreshAction.setStatusTip("Refresh Serial Ports")
        self.refreshAction.triggered.connect(self.__refresh_ports__)

        self.rescaleAxesAction = Action(None, "Rescale Axes", self)
        self.rescaleAxesAction.setShortcut("Ctrl+R")
        self.rescaleAxesAction.setStatusTip("Rescale Plot Axes")
        self.rescaleAxesAction.triggered.connect(self.__rescale_axes__)

        self.resetDevice = Action(None, "Toggle DTR/RTS", self)
        self.resetDevice.setStatusTip("Reset Device")
        self.resetDevice.triggered.connect(self.__reset_device__)

        # Menu to open or close port
        # Toggle port state
        self.openClosePort = None
        if self.port:
            self.openClosePort = Action(None, "Close serial port", self)
            self.openClosePort.setStatusTip("Close serial port")
        else:
            self.openClosePort = Action(None, "Open serial port", self)
            self.openClosePort.setStatusTip("Open serial port")
        self.openClosePort.triggered.connect(self.__open_close_port__)

        self.importSceneAction = Action(None, "Open", self)
        self.importSceneAction.setShortcut("Ctrl+O")
        self.importSceneAction.setStatusTip("Import scene from CSV")
        self.importSceneAction.triggered.connect(self.__import_scene__)

        self.openRawAction = Action(None, "Open Raw CSV", self)
        self.openRawAction.setShortcut("Ctrl+Shift+O")
        self.openRawAction.setStatusTip("Import raw CSV - time as first column, data as other colums (not exported by this tool)")
        self.openRawAction.triggered.connect(self.__open_raw__)

    def __rescale_axes__(self):
        self.plot_page.plot.canvas.getPlotItem().disableAutoRange()
        self.plot_page.plot.canvas.getPlotItem().enableAutoRange()

    def __init_menubar__(self):
        self.menubar_init()
        self.menubar_add_menu("&File")
        self.menu_add_action("&File", self.importSceneAction)
        self.menu_add_action("&File", self.openRawAction)
        self.menu_add_action("&File", self.exportOutputWindowAction)
        self.menu_add_action("&File", self.exitAction)

        self.menubar_add_menu("&View")
        self.menu_add_action("&View", self.rescaleAxesAction)
        self.menu_add_action("&View", self.autoClearPlotAction)

        self.menubar_add_menu("&Serial")
        self.__refresh_ports__()

    def __init_port_menu__(self):
        serial_menu = self.menubar_get_menu("&Serial")
        serial_menu.clear()
        serial_menu.addAction(self.refreshAction)
        ports_submenu = serial_menu.addMenu("&Port")

        # Serial ports submenu
        ports_submenu.addSeparator()
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
                    self.__on_port_changed__(self.port)
                self.ports_action_group.addAction(action)
            self.ports_action_group.setExclusive(True)
        else:
            ports_submenu.setEnabled(False)

        self.__init_baudrate_menu__()
        self.menu_add_action("&Serial", self.resetDevice)
        if len(self.serial_ports) == 0:
            self.resetDevice.setEnabled(False)
        self.menu_add_action("&Serial", self.openClosePort)
        self.__change_menubar_text_open_close_port__()

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

    def log(self, msg):
        cursor = self.log_editor.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(msg + "\n")
        self.log_editor.setTextCursor(cursor)
        self.log_editor.ensureCursorVisible()

    def output(self, msg):
        cursor = self.output_editor.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(msg + "\n")
        self.output_editor.setTextCursor(cursor)
        self.output_editor.ensureCursorVisible()

    def __on_port_changed__(self, newPort):
        if newPort != self.port:
            self.port = newPort
        self.__reopen_serial_port__()
        self.plot_tab.setTabText(0, str(self.port) if self.port is not None else "Port")
        self.__change_menubar_text_open_close_port__()

    def __on_baudrate_changed__(self, newBaudRate):
        if newBaudRate != self.baudrate:
            self.baudrate = newBaudRate
        self.__reopen_serial_port__()
        self.__change_menubar_text_open_close_port__()

    def __refresh_ports__(self):
        self.log("Refreshing serial ports")
        self.serial_ports = list_serial_ports()

        # If the device that was being monitored has
        # now been removed, close the port
        if self.port not in self.serial_ports:
            self.port = None
            if self.serial_port:
                self.serial_port.close()
            self.serial_port = None

        self.__init_port_menu__()
        if len(self.serial_ports) == 0:
            self.resetDevice.setEnabled(False)
            self.log("No serial ports detected")
        else:
            self.resetDevice.setEnabled(True)
            self.log("One or more serial ports detected")

    def __reset_device__(self):
        self.log("Toggling DTR/RTS for device at serial port {}".format(self.port))

        # Close if already open
        if self.serial_port:
            self.serial_port.close()

        # Reset the device by re-opening Serial port
        # with DTR and RTS enabled
        #
        # These are enabled by default
        self.serial_port = serial.Serial(self.port, self.baudrate)
        self.__reopen_serial_port__()
        self.__change_menubar_text_open_close_port__()

    def __clear_plot__(self):
        self.plot_page.plot.plot_item.clear()
        self.plot_page.plot.traces = {}
        self.plot_page.plot.trace_names = []
        self.plot_page.plot.data = {}

    def __open_raw__(self):
        dialog = QFileDialog()
        fmt = "csv"
        dialog.setDefaultSuffix(fmt)
        dialog.setNameFilters([f"{fmt} (*.{fmt})"])

        if dialog.exec_() == QDialog.Accepted:
            path = dialog.selectedFiles()[0]

            # Set plot tab title to filename
            filename = os.path.basename(path)
            self.plot_tab.setTabText(0, filename)
            self.plot_tab.setToolTip(path)

            with open(path, "r") as csvfile:
                reader = csv.reader(csvfile)

                # Clear existing plot and set new header
                self.__clear_plot__()
                self.plot_page.plot.legend.clear()

                # Parse Header
                # Expected: Time, Foo, Bar, Baz, ...
                # Note: first line (header) may be optionally prepended with %
                # Convert to: "Foo","Bar",...
                header = [h.replace('%', '').strip() for h in next(reader)]
                header = list(dict.fromkeys(header))
                self.plot_page.plot.set_header(header)

                dataset = []
                for row in reader:
                    time = float(row[0])
                    signals = [float(x) for x in row[1:]]
                    data = []
                    data.append(time)
                    data.extend(signals)
                    dataset.append(data)
                self.plot_page.plot.update_data(dataset)
                self.log("Successfully imported from '{}'".format(path))

    def __import_scene__(self):
        dialog = QFileDialog()
        fmt = "csv"
        dialog.setDefaultSuffix(fmt)
        dialog.setNameFilters([f"{fmt} (*.{fmt})"])

        if dialog.exec_() == QDialog.Accepted:
            path = dialog.selectedFiles()[0]

            # Set plot tab title to filename
            filename = os.path.basename(path)
            self.plot_tab.setTabText(0, filename)
            self.plot_tab.setToolTip(path)

            with open(path, "r") as csvfile:
                reader = csv.reader(csvfile)

                # Clear existing plot and set new header
                self.__clear_plot__()
                self.plot_page.plot.legend.clear()

                # Parse Header
                # Expected: "Foo_x","Foo_y","Bar_x","Bar_y",...
                # Convert to: "Foo","Bar",...
                header = ["_".join(h.strip().split("_")[:-1]) for h in next(reader)]
                header = list(dict.fromkeys(header))
                header.insert(0, "Time")
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
                self.log("Successfully imported from '{}'".format(path))

    # window functions
    def __center_window__(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def __reopen_force_gauge_serial_port__(self):
        # Close if already open
        if self.force_gauge_serial_port:
            self.force_gauge_serial_port.close()
            self.log("Closed force_gauge serial port")

        # try to find the right serial port
        force_gauge_ports = list_serial_ports_by_descriptors(["Mark-10"])

        if len(force_gauge_ports) == 1:
            self.force_gauge_port = force_gauge_ports[0]
        elif len(force_gauge_ports) > 1:
            self.log("Too many gauge ports found: {}".format(force_gauge_ports))
            return
        else:
            self.log("No force gauge ports found!")
            return

        # Open serial_port
        if self.force_gauge_port and self.force_gauge_baudrate:
            self.log("Opening force_gauge serial port {}, baud={}".format(self.force_gauge_port, self.force_gauge_baudrate))
            self.force_gauge_serial_port = serial.Serial()
            self.force_gauge_serial_port.port = self.force_gauge_port
            self.force_gauge_serial_port.baudrate = self.baudrate
            # Disable hardware flow control
            self.force_gauge_serial_port.setRTS(False)
            self.force_gauge_serial_port.setDTR(False)
            try:
                self.force_gauge_serial_port.open()
                # write a '?' to queue data
                self.force_gauge_serial_port.write(b'?\r')
            except Exception as e:
                self.log(str(e))

    def __reopen_serial_port__(self):
        self.__reopen_force_gauge_serial_port__()

        # Close if already open
        if self.serial_port:
            self.serial_port.close()
            self.log("Closed serial port")

        # Open serial_port
        if self.port and self.baudrate:
            self.log("Opening serial port {}, baud={}".format(self.port, self.baudrate))
            self.serial_port = serial.Serial()
            self.serial_port.port = self.port
            self.serial_port.baudrate = self.baudrate
            # Disable hardware flow control
            self.serial_port.setRTS(False)
            self.serial_port.setDTR(False)
            try:
                self.serial_port.open()
            except Exception as e:
                self.log(str(e))

    def __update_plot__(self):
        def escape_ansi(line):
            ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
            return ansi_escape.sub("", str(line))

        if not self.serial_port:
            return

        try:
            if self.serial_port.inWaiting() == 0:
                return  # do nothing
        except:
            return

        # read a line from serial port
        strdata = self.serial_port.readline()

        if self.force_gauge_serial_port:
            force_gauge_data = self.force_gauge_serial_port.readline()
            try:
                self.force_gauge_value = float(force_gauge_data.split()[0])
            except:
                print("Could not parse force gauge string: '{}'".format(force_gauge_data))
            # write a '?' to queue data
            self.force_gauge_serial_port.write(b'?\r')

        # and decode it
        if sys.version_info >= (3, 0):
            strdata = strdata.decode("utf-8", "backslashreplace")

        strdata = escape_ansi(strdata)
        strdata = strdata.strip()
        self.output(strdata)
        arrdata = strdata.split(",")

        # There must be at least 2 columns
        # Time,Signal_1
        # Then it is (possibly) a valid timeseries
        if len(arrdata) < 2:
            return

        # determine if this line is a header or not
        # The line must start with `%`
        is_header = False
        if strdata.startswith("%"):
            is_header = True

        if is_header:
            # an array of strings

            # Clear existing plot and set new header
            if self.auto_clear_plot_on_header_change:
                self.__clear_plot__()
                self.plot_page.plot.legend.clear()

            arrdata[0] = arrdata[0][1:]  # remove %
            # add the force gauge header
            arrdata.push_back(self.force_gauge_header)
            self.plot_page.plot.set_header(arrdata)
        else:
            # an array of numbers
            try:
                datapoint = [float(x.strip()) for x in arrdata]
                # add the force gauge value
                datapoint.push_back(self.force_gauge_value)

                if len(self.plot_page.plot.trace_names) == len(datapoint):
                    # This is a good datapoint
                    # Matches the exact number of cols as the header
                    self.plot_page.plot.update_data([datapoint])
                else:
                    # Ignore it, this is not a valid datapoint
                    # datapoint could be an empty list
                    self.log("Not a valid datapoint: '{}'".format(strdata))
            except:
                pass

    def __open_close_port__(self):
        if self.serial_port.is_open:
            self.serial_port.close()
            self.log("Closed serial port")
            self.openClosePort.setText("Open " + str(self.port))
            self.openClosePort.setToolTip("Open serial port")
        else:
            try:
                self.serial_port.open()
            except Exception as e:
                self.log(str(e))
                return
            self.log("Opened serial port")
            self.openClosePort.setText("Close " + str(self.port))
            self.openClosePort.setToolTip("Close serial port")

    def __change_menubar_text_open_close_port__(self):
        if self.serial_port:
            self.openClosePort.setDisabled(False)
            if self.serial_port.is_open:
                self.openClosePort.setText("Close " + str(self.port))
                self.openClosePort.setToolTip("Close serial port")
            else:
                self.openClosePort.setText("Open " + str(self.port))
                self.openClosePort.setToolTip("Open serial port")
        else:
            self.openClosePort.setText("Open serial port")
            self.openClosePort.setToolTip("Open serial port")
            self.openClosePort.setDisabled(True)

    def __on_auto_clear_plot_action__(self):
        if self.autoClearPlotAction.isChecked():
            self.log("Clear plot on reset is enabled")
            self.auto_clear_plot_on_header_change = True
        else:
            self.log("Clear plot on reset is disabled")
            self.auto_clear_plot_on_header_change = False

    def __save_received_data_to_file__(self):
        name = QtWidgets.QFileDialog.getSaveFileName(self, "Save file", ".", "*.txt;;*")
        if len(name) > 0 and name[0] != '':
            with open(name[0], "w") as file:
                file.write(self.output_editor.toPlainText())
