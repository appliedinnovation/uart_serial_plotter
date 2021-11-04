import pyqtgraph as pg
import numpy as np
from PyQt5.QtWidgets import QGraphicsView


class Plot(object):
    def __init__(self, header=None, data=None):

        self.traces = dict()
        self.data = dict()
        self.trace_names = []
        self.canvas = pg.PlotWidget()
        self.canvas.setAntialiasing(False)
        self.canvas.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing)
        self.plot_item = self.canvas.getPlotItem()

        if header:
            self.set_header(header)
        if data:
            self.set_data(data)

        self.legend = self.canvas.addLegend()

    def set_header(self, header_names):
        self.trace_names = header_names

    def update_data(self, data):
        self.legend.clear()

        for name in self.trace_names:
            # initialize the data for this trace
            if name not in self.data:
                self.data[name] = {"x": [0], "y": [0]}

        for row in data:
            time = row[0]
            # skip the first value (since we assume it is time)
            for i in range(1, len(self.trace_names)):
                self.data[self.trace_names[i]]["x"].append(time)
                self.data[self.trace_names[i]]["y"].append(row[i])

        # now actually plot the data
        for i, name in enumerate(self.trace_names):
            self.plot_item.addItem(
                pg.PlotDataItem(
                    self.data[name]["x"],
                    self.data[name]["y"],
                    pen=(i, len(self.trace_names)),
                    name=name,
                )
            )
