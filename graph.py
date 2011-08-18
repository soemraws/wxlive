from matplotlib.axes import Axes
import axes as ax

def axes_set_x_variable(axes, x_variable, interval = None):
  '''Enable the axes to plot wxlive.Variables. The x_variable is the
     wxlive.Variable whose value is assumed to be the x value. If interval is
     provided, the axes will automatically query the x_variable with that
     interval.'''
  method = type(axes.plot)
  if interval:
    ax.make_axes_self_updating(axes, interval)
    axes.update = method(ax.axes_self_updating_update, axes,
        Axes)
  else:
    ax.make_axes_live(axes)
    axes.update = method(ax.axes_update, axes, Axes)
    axes.event_handler = ax.AxesEvtHandler(axes)
    x_variable.add_listener(axes)
    axes.reset_plots()
  
  axes._x_variable = x_variable
  axes._x_variable_id = x_variable.id

  return axes


def axes_set_time_as_x_variable(axes, interval, time_offset = 0.0):
  '''Enable the axes to plot wxlive.Variables. The x value for
  Variables is assumed to be the time.'''
  ax.make_axes_self_updating(axes, interval)
  
  method = type(axes.plot)
  axes.update = method(ax.axes_time_update, axes, Axes)
  axes.set_time_offset = method(ax.axes_set_time_offset, axes, Axes)
  axes.get_time_offset = method(ax.axes_get_time_offset, axes, Axes)
  axes.reset_time_offset = method(ax.axes_reset_time_offset, axes, Axes)

  axes.set_time_offset(time_offset)


# vim: set filetype=python shiftwidth=2 softtabstop=2 tabstop=8 expandtab: 

