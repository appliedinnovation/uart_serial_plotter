import functools
import re
import serial
import serial.tools.list_ports

import sys

if sys.platform.startswith("win"):
    from uart_serial_plotter.usb_device_listener_windows import UsbDeviceChangeMonitor
elif sys.platform.startswith("linux"):
    # not implemented
    pass
else:
    raise ImportError(
        "This module does not support this platform '{}'".format(sys.platform)
    )

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

from uart_serial_plotter.action import Action
from uart_serial_plotter.pages import PlotPage
from uart_serial_plotter.list_serial_ports import list_serial_ports
import csv
from uart_serial_plotter.tabs import Tabs


class MainWindow(QMainWindow):

    from uart_serial_plotter.menubar import (
        menubar_init,
        menubar_add_menu,
        menubar_get_menu,
        menu_add_action,
    )

    def __init__(self):
        super().__init__()

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
            self.log_info("Current port: " + str(self.port))
            self.__reopen_serial_port__()
        else:
            self.log_warning("No device connected")

        if sys.platform.startswith("win"):
            # TODO(pranav): Implement this class for Linux
            UsbDeviceChangeMonitor(
                self.__on_usb_device_arrival__, self.__on_usb_device_removal__
            )

        self.update_timer = QtCore.QTimer(timerType=0)  # Qt.PreciseTimer
        self.update_timer.timeout.connect(self.__update_plot__)
        self.update_timer.start(33)

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
        self.plot_tab.addTab(self.plot_page, str(self.port) if self.port is not None else "Port")
        self.plot_tab.setTabText(0, str(self.port) if self.port is not None else "Port")
        self.plot_tab.setStyleSheet(
            "QTabBar::tab:selected {background: white; color: black;}"
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
            "QTabBar::tab:selected {background: white; color: black;}"
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

        self.importSceneAction = Action(None, "Open", self)
        self.importSceneAction.setShortcut("Ctrl+O")
        self.importSceneAction.setStatusTip("Import scene from CSV")
        self.importSceneAction.triggered.connect(self.__import_scene__)

    def __rescale_axes__(self):
        self.plot_page.plot.canvas.getPlotItem().disableAutoRange()
        self.plot_page.plot.canvas.getPlotItem().enableAutoRange()

    def __init_menubar__(self):
        self.menubar_init()
        self.menubar_add_menu("&File")
        self.menu_add_action("&File", self.importSceneAction)
        self.menu_add_action("&File", self.exitAction)

        self.menubar_add_menu("&View")
        self.menu_add_action("&View", self.rescaleAxesAction)

        self.menubar_add_menu("&Serial")
        self.__refresh_ports__()

    def __init_port_menu__(self):
        serial_menu = self.menubar_get_menu("&Serial")
        serial_menu.clear()
        ports_submenu = serial_menu.addMenu("&Port")

        # Serial ports submenu
        ports_submenu.addAction(self.refreshAction)
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
                    if self.plot_tab:
                        self.plot_tab.setTabText(0, str(self.port) if self.port is not None else "Port")
                    self.__on_port_changed__(self.port)
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

    def log(self, color, msg):
        # Append received data to log window
        cursor = self.log_editor.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertHtml(
            """
            <div style='color:{};'>
            {}
            <br/>
            </div>""".format(
                color, msg
            )
        )

    def log_error(self, msg):
        self.log("#FF073A", msg)

    def log_warning(self, msg):
        self.log("#FFC42E", msg)

    def log_info(self, msg):
        self.log("white", msg)

    def __on_port_changed__(self, newPort):
        if newPort != self.port:
            self.port = newPort
        self.__reopen_serial_port__()

    def __on_baudrate_changed__(self, newBaudRate):
        if newBaudRate != self.baudrate:
            self.baudrate = newBaudRate
        self.__reopen_serial_port__()

    def __refresh_ports__(self):
        self.log_info("Refreshing serial ports")
        self.serial_ports = list_serial_ports()
        self.__init_port_menu__()
        if len(self.serial_ports) == 0:
            self.resetDevice.setEnabled(False)
            self.log_warning("No serial ports detected")
        else:
            self.resetDevice.setEnabled(True)
            self.log_info("One or more serial ports detected")

    def __reset_device__(self):
        self.log_info("Toggling DTR/RTS for device at serial port {}".format(self.port))

        # Close if already open
        if self.serial_port:
            self.serial_port.close()

        # Reset the device by re-opening Serial port
        # with DTR and RTS enabled
        #
        # These are enabled by default
        self.serial_port = serial.Serial(self.port, self.baudrate)
        self.__reopen_serial_port__()

    def __clear_plot__(self):
        self.plot_page.plot.plot_item.clear()
        self.plot_page.plot.traces = {}
        self.plot_page.plot.trace_names = []
        self.plot_page.plot.data = {}

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
                self.log_info("Successfully imported from '{}'".format(path))

    # window functions
    def __center_window__(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def __reopen_serial_port__(self):
        # Close if already open
        if self.serial_port:
            self.serial_port.close()
            self.log_info("Closed serial port")

        # Open serial_port
        if self.port and self.baudrate:
            self.log_info(
                "Opening serial port {}, baud={}".format(self.port, self.baudrate)
            )
            self.serial_port = serial.Serial()
            self.serial_port.port = self.port
            self.serial_port.baudrate = self.baudrate
            # Disable hardware flow control
            self.serial_port.setRTS(False)
            self.serial_port.setDTR(False)
            self.serial_port.open()

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

        # and decode it
        if sys.version_info >= (3, 0):
            strdata = strdata.decode("utf-8", "backslashreplace")

        escaped_strdata = escape_ansi(strdata)

        def strdata_as_html():
            nonlocal strdata
            nonlocal escaped_strdata

            split_ANSI_escape_sequences = re.compile(
                r"""
                (?P<col>(\x1b     # literal ESC
                \[       # literal [
                [;\d]*   # zero or more digits or semicolons
                [A-Za-z] # a letter
                )*)
                (?P<name>.*)
                """,
                re.VERBOSE,
            ).match

            # print(repr(escaped_strdata))
            num_newlines = escaped_strdata.count("\n")

            def generate_break(n):
                return "".join(["<br/>" for i in range(n)])

            group_dict = split_ANSI_escape_sequences(strdata).groupdict()
            if "col" in group_dict:
                # There is an ANSI color code
                color_code = repr(group_dict["col"])

                if group_dict["col"] != "":

                    ANSI_FOREGROUND_COLOR_MAP = {
                        "\x1b[0;30m": "#000000",  # Black
                        "\x1b[0;31m": "#FF073A",  # Red
                        "\x1b[0;32m": "#1FFF0F",  # Green
                        "\x1b[0;33m": "#FFC42E",  # Yellow
                        "\x1b[0;34m": "#4D4DFF",  # Blue
                        "\x1b[0;35m": "#EA00FF",  # Magenta
                        "\x1b[0;36m": "#00FFFF",  # Cyan
                        "\x1b[0;37m": "#FBFFFF",  # White
                    }

                    # Check if ANSI color code is specified using:
                    # \x1B[38;2;R;G;Bm
                    #
                    # This is any RGB color (with values in [0-255])
                    any_rgb_color = str("\x1b[38;2;")
                    color_code_str = str(group_dict["col"])
                    if any_rgb_color in color_code_str:
                        color_split = color_code_str.split(any_rgb_color)
                        r, g, b = color_split[1].split(";")
                        b = b.split("m")[0]
                        r, g, b = [int(i) for i in (r, g, b)]

                        BASIC_COLORS = {
                            (255, 255, 255): "#FBFFFF",  # Neon white
                            (255, 0, 0): "#FF073A",  # Neon red
                            (0, 255, 0): "#1FFF0F",  # Neon green
                            (0, 0, 255): "#4D4DFF",  # Neon blue
                        }

                        strdata = ""
                        if (r, g, b) in BASIC_COLORS:
                            # Replace (r,g,b) with neon variant which is more suitable for dark mode
                            strdata = "<div style='color:{};'>".format(
                                BASIC_COLORS[(r, g, b)]
                            )
                        else:
                            # Not a basic color, use exact RGB as received
                            strdata = "<div style='color:rgb({},{},{});'>".format(r, g, b)
                        strdata += (
                            escaped_strdata.strip()
                            + generate_break(num_newlines)
                            + "</div>"
                        )
                    else:
                        found_color = False
                        for c in ANSI_FOREGROUND_COLOR_MAP:
                            if color_code == repr(c):
                                if c in strdata:
                                    strdata = (
                                        "<div style='color:{};'>".format(
                                            ANSI_FOREGROUND_COLOR_MAP[c]
                                        )
                                        + escaped_strdata.strip()
                                        + generate_break(num_newlines)
                                        + "</br>"
                                    )
                                    found_color = True
                                    break
                        if not found_color:
                            strdata = "<div style='color:#FBFFFF;'>{}{}</div>".format(
                                escaped_strdata, generate_break(num_newlines)
                            )
                else:
                    strdata = "<div style='color:#FBFFFF;'>{}{}</div>".format(
                        escaped_strdata, generate_break(num_newlines)
                    )
            else:
                strdata = "<div style='color:#FBFFFF;'>{}{}</div>".format(
                    escaped_strdata, generate_break(num_newlines)
                )

            # Strip all ANSI style characters
            ANSI_STYLES = {
                "\x1b[m",
                "\x1b[0m",  # Reset
                "\x1b[1m",  # Bold
                "\x1b[2m",  # Faint
                "\x1b[3m",  # Italic
                "\x1b[4m",  # Underlined
                "\x1b[7m",  # Inverse
                "\x1b[9m",  # Strikethrough
            }

            for style in ANSI_STYLES:
                if style in strdata:
                    strdata = strdata.replace(style, "")

            # Append received data to GUI output window
            cursor = self.output_editor.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertHtml(strdata)
            self.output_editor.setTextCursor(cursor)
            self.output_editor.ensureCursorVisible()

        # Update output editor text with a one-shot timer
        QtCore.QTimer.singleShot(0, strdata_as_html)

        arrdata = escaped_strdata.strip().split(",")

        # There must be at least 2 columns
        # Time,Signal_1
        # Then it is (possibly) a valid timeseries
        if len(arrdata) < 2:
            return

        # determine if this line is a header or not (first value is string data)
        is_header = False
        try:
            dummy = float(arrdata[0])
        except ValueError:
            is_header = True

        if is_header:
            # an array of strings
            self.__clear_plot__()
            self.plot_page.plot.set_header(arrdata)
        else:
            # an array of numbers
            try:
                datapoint = [float(x.strip()) for x in arrdata]

                if len(self.plot_page.plot.trace_names) == 0 or len(
                    self.plot_page.plot.trace_names
                ) < len(datapoint):
                    # Header not set
                    # Maybe we didn't receive it over UART
                    # Set the Header to be: "Time","Signal_1", "Signal_2",...
                    header = ["Time"]
                    header.extend(
                        ["Signal_" + str(i) for i in range(len(datapoint) - 1)]
                    )
                    self.plot_page.plot.set_header(header)
                    self.plot_page.plot.update_data([datapoint])
                elif len(self.plot_page.plot.trace_names) == len(datapoint):
                    # This is a good datapoint
                    # Matches the exact number of cols as the header
                    self.plot_page.plot.update_data([datapoint])
                else:
                    # Ignore it, this is not a valid datapoint
                    # datapoint could be an empty list
                    self.log_info(
                        "Not a valid datapoint: '{}'".format(escaped_strdata.strip())
                    )
            except:
                pass

    def __on_usb_device_arrival__(self):
        self.log_info("Detected New USB Device")
        self.__refresh_ports__()

    def __on_usb_device_removal__(self):
        self.log_info("Detected USB Device Removal")
        self.__refresh_ports__()
