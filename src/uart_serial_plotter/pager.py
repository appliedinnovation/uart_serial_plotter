from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
)
from PyQt5.QtCore import pyqtSignal, pyqtSlot


class Pager(QWidget):
    finished = pyqtSignal()
    changed = pyqtSignal(int)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        lay = QVBoxLayout(self)

        self.stack = QStackedWidget()
        self.stack.currentChanged.connect(self.onChanged)

        self.nextButton = QPushButton("Next")
        self.nextButton.clicked.connect(self.onNext)
        self.finishButton = QPushButton("Finish")
        self.finishButton.clicked.connect(self.onFinish)
        self.previousButton = QPushButton("Previous")
        self.previousButton.clicked.connect(self.onPrevious)
        self.disableControls()
        self.btnLayout = QHBoxLayout()
        self.btnLayout.addWidget(self.previousButton)
        self.btnLayout.addWidget(self.nextButton)
        self.btnLayout.addWidget(self.finishButton)

        lay.addWidget(self.stack)
        lay.addLayout(self.btnLayout)

    # events
    @pyqtSlot()
    def onNext(self):
        index = self.stack.currentIndex()
        top = self.stack.count() - 1
        index += 1
        if index >= top:
            index = top
        self.stack.setCurrentIndex(index)

    @pyqtSlot()
    def onPrevious(self):
        index = self.stack.currentIndex()
        bottom = 0
        index -= 1
        if index <= bottom:
            index = bottom
        self.stack.setCurrentIndex(index)

    @pyqtSlot()
    def onFinish(self):
        self.disableFinish()
        self.disablePrevious()
        self.enableNext()
        self.finished.emit()
        self.stack.setCurrentIndex(0)

    @pyqtSlot(int)
    def onChanged(self, index):
        self.disableControls()
        self.changed.emit(index)
        widget = self.stack.widget(index)
        widget.onEnter()
        if widget.nextEnabled:
            self.enableNext()
        if widget.previousEnabled:
            self.enablePrevious()

    @pyqtSlot()
    def onPageFinished(self):
        self.disableControls()

        index = self.stack.currentIndex()
        top = self.stack.count() - 1
        bottom = 0

        self.enableNext()
        if index >= top:
            self.disableNext()
            self.enableFinish()

        self.enablePrevious()
        if index <= bottom:
            self.disablePrevious()

    # previous/next/finish controls
    def enableNext(self):
        self.nextButton.show()

    def enableFinish(self):
        self.finishButton.show()

    def enablePrevious(self):
        self.previousButton.show()

    def enableControls(self):
        self.enableNext()
        self.enableFinish()
        self.enablePrevious()

    def disableNext(self):
        self.nextButton.hide()

    def disableFinish(self):
        self.finishButton.hide()

    def disablePrevious(self):
        self.previousButton.hide()

    def disableControls(self):
        self.disableNext()
        self.disableFinish()
        self.disablePrevious()

    # for adding widgets and controlling page
    def addPage(self, pageWidget):
        pageWidget.setPager(self)
        self.stack.addWidget(pageWidget)
        pageWidget.finished.connect(self.onPageFinished)

    def getButtonHeight(self):
        return self.btnLayout.sizeHint().height()

    def clearPages(self):
        self.stack.clear()

    def setPageIndex(self, index):
        self.stack.setCurrentIndex(index)
