from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QVBoxLayout,
    QMessageBox,
    QErrorMessage,
    QScrollArea,
    QSizePolicy,
)
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QSize, Qt

import resource

# from progress import ProgressBar


class BasePage(QWidget):
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._pager = None
        self.nextEnabled = True
        self.previousEnabled = True
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored))

        self.setStyleSheet("QLabel {font: 20pt}")

        self.labels = []
        self.picture = None

    @pyqtSlot()
    def onEnter(self):
        pass

    def setPager(self, pager):
        self._pager = pager

    def getButtonHeight(self):
        if self._pager is not None:
            return self._pager.getButtonHeight()
        else:
            return 100

    @pyqtSlot()
    def onExit(self):
        pass

    def getPictureSize(self):
        s = self.size() - QSize(0, self.getButtonHeight())
        for l in self.labels:
            s -= QSize(0, l.size().height())
        return QSize(max(400, s.width()), max(400, s.height()))

    def resizeEvent(self, event):
        if self.picture is not None:
            i = self.layout.indexOf(self.picture)
            self.layout.removeWidget(self.picture)
            self.picture.setParent(None)
            self.picture = QLabel(self)
            self.picture.setPixmap(
                self.pixMap.scaled(self.getPictureSize(), Qt.KeepAspectRatio)
            )
            self.layout.insertWidget(i, self.picture)


class StartPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.previousEnabled = False

        # self.pixMap = QtGui.QPixmap(resource.path("images/cable.jpg"))

        title = QLabel("Welcome to SmartDrive MX2+ Programming")
        cableLabel = QLabel(
            "Plug in the programming cables to the SmartDrive as shown below.\nMake sure the SmartDrive is OFF.\nRefer to the 'Help' menu for BLE setup instructions."
        )
        cableLabel.setWordWrap(True)
        self.labels = [title, cableLabel]

        # self.picture = QLabel(self)
        # self.picture.setPixmap(
        #     self.pixMap.scaled(self.getPictureSize(), Qt.KeepAspectRatio)
        # )

        self.layout.addWidget(title)
        self.layout.addWidget(cableLabel)
        self.layout.addWidget(self.picture)

    @pyqtSlot()
    def onEnter(self):
        super().finished.emit()
