import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import time

class TYPlot(object):
  def __init__(self, axes, y_variable, *args, **kwargs):
    self.plot = axes.plot([], [], *args, **kwargs)[0]
    self.y_variable = y_variable
    self.x_data = []
    self.y_data = []

  def reset(self):
    self.x_data = []
    self.y_data = []

  def update(self, x, max_points=None):
    self.update_with_value(x, self.y_variable.value, max_points)

  def update_with_value(self, x, y, max_points=None):
    self.x_data.append(x)
    self.y_data.append(y)

    self.update_plot(max_points)

  def update_plot(self, max_points=None):
    if max_points and len(self.x_data) > max_points:
      self.x_data = self.x_data[1:]
      self.y_data = self.y_data[1:]

    self.plot.set_xdata(self.x_data)
    self.plot.set_ydata(self.y_data)

class XYPlot(TYPlot):
  def __init__(self, axes, x_variable, y_variable, max_points = 100000, *args, **kwargs):
    TYPlot.__init__(self, axes = axes, y_variable = y_variable, *args, **kwargs)
    self.x_variable = x_variable

  def update(self, *args, **kwargs):
    self.update_with_value(self.x_variable.value, self.y_variable.value, **kwargs)

class StripChart(FigureCanvasWxAgg):
  def __init__(self, parent, id, max_points=100000, dpi=100, axes=None, title=None):
    self.figure = Figure((3.0, 3.0), dpi=dpi)
    self.axes = axes
    self._plots = {}
    self.time_offset = time.time()
    self.max_points = int(max_points)

    if not self.axes:
      self.axes = self.figure.add_subplot(111)
      self.axes.set_axis_bgcolor('black')
    if title:
      self.axes.set_title(title, size=12)

    FigureCanvasWxAgg.__init__(self, parent, id, self.figure)

  def add_plot(self, variable, *args, **kwargs):
    self._plots[variable.id] = TYPlot(self.axes, variable, *args, **kwargs)

  def remove_plot(self, variable_id):
    del self._plots[variable_id]

  def set_bounds(self, xmin=None, xmax=None, ymin=None, ymax=None):
    self.axes.set_xbound(lower=xmin, upper=xmax)
    self.axes.set_ybound(lower=ymin, upper=ymax)

  def on_live_variable_event(self, x):
    id = x.GetId()
    if id in self._plots:
      t = x.time - self.time_offset
      for var_id, plot in self._plots.iteritems():
        if id == var_id:
          plot.update_with_value(t, x.value, max_points=self.max_points)
        else:
          plot.update(t, max_points=self.max_points)
      self.draw()

# vim: set shiftwidth=2 softtabstop=2 tabstop=8 expandtab: 

