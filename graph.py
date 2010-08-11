import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import numpy

class Plot(object):
  def __init__(self, parent, id, color, linewidth=1):
    self.plot = parent.plot([], linewidth=linewidth, color=color)[0]
    self.max_data = 10000
    self.x_data = []
    self.y_data = []

  def reset(self):
    self.x_data = []
    self.y_data = []
    self.set_xdata(self.x_data)
    self.set_ydata(self.y_data)

  def update(self, x, y):
    self.x_data.append(x)
    self.y_data.append(y)

    if len(self.x_data) > self.max_data:
      self.x_data = self.x_data[1:]
      self.y_data = self.y_data[1:]

    self.plot.set_xdata(numpy.array(self.x_data))
    self.plot.set_ydata(numpy.array(self.y_data))

class Graph(FigureCanvasWxAgg):
  def __init__(self, parent, id=-1, dpi=100, axes=None, x_offset = 0.0,
      title=None):
    self.figure = Figure((3.0, 3.0), dpi=dpi)
    self.axes = axes
    self._plots = {}
    self.x_offset = x_offset

    if not self.axes:
      self.axes = self.figure.add_subplot(111)
      self.axes.set_axis_bgcolor('black')
    if title:
      self.axes.set_title(title, size=12)

    FigureCanvasWxAgg.__init__(self, parent, id, self.figure)

  def add_plot(self, variable_id, linewidth, color):
    self._plots[variable_id] = Plot(self.axes, variable_id,
        color, linewidth)

  def remove_plot(self, variable_id):
    del self._plots[variable_id]

  def set_bounds(self, xmin=None, xmax=None, ymin=None, ymax=None):
    self.axes.set_xbound(lower=xmin, upper=xmax)
    self.axes.set_ybound(lower=ymin, upper=ymax)

  def on_live_variable_event(self, x):
    id = x.GetId()
    if id in self._plots:
      self._plots[id].update(x.time - self.x_offset, x.value)
      self.draw()

# vim: set shiftwidth=2 softtabstop=2 tabstop=8 expandtab: 

