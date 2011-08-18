from matplotlib.axes import Axes
from wx import EvtHandler
from wxlive import Variable
from time import sleep, time
from threading import Thread

class AxesEvtHandler(EvtHandler):
  '''An event handler so that the axes can appear to work as listeners'''
  def __init__(self, axes, *args, **kwargs):
    EvtHandler.__init__(self, *args, **kwargs)
    self._axes = axes

  def on_live_variable_event(self, evt):
    self._axes.update(evt.value)

class Plot(object):
  def __init__(self, axes, *args, **kwargs):
    self._plot = axes._orig_plot([], [], *args, **kwargs)[0]
    self._x_data = []
    self._y_data = []

  @property
  def plot(self):
    return self._plot

  @property
  def xdata(self):
    return self._x_data

  @property
  def ydata(self):
    return self._y_data

  def reset(self):
    self._x_data = []
    self._y_data = []

    self.update_plot()

  def update_plot(self, max_points=None):
    dlen = len(self._x_data)
    if max_points and dlen > max_points:
      dif = dlen - max_points
      self._x_data = self._x_data[dif:]
      self._y_data = self._y_data[dif:]

    self.plot.set_xdata(self._x_data)
    self.plot.set_ydata(self._y_data)


class VariablePlot(Plot):
  def __init__(self, axes, y_variable, *args, **kwargs):
    Plot.__init__(self, axes, *args, **kwargs)
    self._y_variable = y_variable

  def update(self, x, max_points=None):
    self._x_data.append(x)
    self._y_data.append(self._y_variable.value)

    self.update_plot(max_points)

  @property
  def y_variable(self):
    return self._y_variable




def find_next_plot(args, start, was_var):
  '''Go through a list of arguments and find the next index
  where a new plot starts.
  '''
  item = args[start]
  for i in range(start+1,len(args)):
    if isinstance(args[i], str):
      return i + 1
    elif isinstance(args[i], Variable) or \
        isinstance(item, Variable)  or \
        i > start + 1:
      return i
  return len(args)

def axes_plot(axes, *args, **kwargs):
  '''Use the standard matplotlib.axes.Axes.plot syntax, with the additional
  ability of, instead of giving arrays, to give wxlive.Variables.'''
  i = 0
  result = []
  while i < len(args):
    if isinstance(args[i], Variable):
      j = find_next_plot(args, i, True)
      if j > i:
        p = VariablePlot(axes, *args[i:j], **kwargs)
        axes._plots[args[i]] = p
        result.append(p.plot)
        i = j
      else:
        return
    else:
      j = find_next_plot(args, i, False)
      p = axes._orig_plot(*args[i:j], **kwargs)
      result.append(p)
      i = j
  return result

def axes_reset_plots(axes):
  for plot in axes._plots.itervalues():
    plot.reset()
  axes.figure.canvas.draw()

def make_axes_live(axes):
  axes._plots = {}
  axes.max_points = None

  method = type(axes.plot)
  axes._orig_plot = axes.plot
  axes.plot = method(axes_plot, axes, Axes)
  axes.reset_plots = method(axes_reset_plots, axes, Axes)

  return axes

def axes_update(axes, x):
  for plot in axes._plots.itervalues():
    plot.update(x, axes.max_points)
  axes.figure.canvas.draw()

def axes_self_updating_update(axes):
  x = axes._x_variable.value
  for plot in axes._plots.itervalues():
    plot.update(x, axes.max_points)
  axes.figure.canvas.draw()

def axes_self_updating_run(axes):
  while axes._continue:
    axes.update()
    if axes._interval:
      sleep(axes._interval)

def axes_self_updating_is_active(axes):
  return axes._thread is not None

def axes_self_updating_start(axes, interval = None):
  if interval:
    axes._interval = float(interval)

  if not axes.is_active():
    axes._continue = True
    axes._thread = Thread(target=axes._run)
    axes._thread.start()

def axes_self_updating_stop(axes):
  if axes._thread:
    axes._continue = False
    axes._thread.join()
    axes._thread = None

def axes_get_interval(axes):
  return axes._interval

def axes_set_interval(axes, value):
  if type(value) != float and type(value) != int:
    raise TypeError('Interval can only be a real number.')
  axes._interval = float(value)

def make_axes_self_updating(axes, interval):
  make_axes_live(axes)
  
  axes._interval = float(interval)
  axes._thread = None
  axes._continue = False

  method = type(axes.plot)
  axes.start = method(axes_self_updating_start, axes,
      Axes)
  axes.stop = method(axes_self_updating_stop, axes,
      Axes)
  axes.is_active = method(axes_self_updating_is_active, axes,
      Axes)
  axes._run = method(axes_self_updating_run, axes,
      Axes)

  return axes

def axes_set_time_offset(axes, value):
  if value == 'now':
    value = time()
  elif type(value) != float and type(value) != int:
    raise TypeError('Interval can only be a real number.')

  axes._time_offset = float(value)

def axes_get_time_offset(axes):
  return axes._time_offset

def axes_reset_time_offset(axes, value=None):
  if not value:
    value = 'now'
  axes.set_time_offset(value)

def axes_time_update(axes):
  t = time() - axes._time_offset
  for plot in axes._plots.itervalues():
    plot.update(t, axes.max_points)
  axes.figure.canvas.draw()


# vim: set filetype=python shiftwidth=2 softtabstop=2 tabstop=8 expandtab: 

