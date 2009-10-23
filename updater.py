import wx
import time
import numpy
import threading
import wx.lib.newevent
import types

# Event sent to widgets, containing the data that they can or may process.

DataReadyEvent, EVT_DATA_READY = wx.lib.newevent.NewEvent()

ID_DATA_READY = 0	# Data from a getter command
ID_DATA_REPLY = 1	# A reply received after a setter command

class Base(list):
  """Base

  This is the base class of all updating properties and not useful by itself.
  It allows widgets to register with the updating property property, and
  defines an easy way to propagate information to all registered widgets.
  """
  def __init__(self, **kwargs):
    super(Base, self).__init__(**kwargs)

  def register(self, widget):
    """register(widget)

    Register a widget with the object. All widgets that are registered with
    the property will receive a EVT_DATA_READY event when the property has
    data to share.
    """
    if self.count(widget) is 0:
      self.append(widget)

  def unregister(self, widget=None):
    """unregister(widget)

    Remove a widget from the list of registered widgets. The widget will not
    receive the EVT_DATA_READY event any more. If no widget is given, all
    registered widgets are unregistered.
    """
    if widget is None:
      del self[:]
    else:
      self.remove(widget)

  def post_event(self, event):
    """post_event(event)
    
    Post event to all registered widgets. This is used internally during
    getting or setting the property value, but might be useful otherwise.
    """
    for w in self:
      try:
        wx.PostEvent(w,event)
      except (KeyboardInterrupt, SystemExit):
        raise
      except:
        self.unregister(w)


class Setter(Base):
  """Setter

  A Setter property simply allows to set a value on a device or object by
  calling its setter function. The reply is then propagated to all widgets
  that know how to handle it.
  """
  def __init__(self, func = None, **kwargs):
    """__init__(setter):

    setter: A setter function to call. The setter function can take any amount
    of arguments.
    """
    super(Setter, self).__init__(**kwargs)
    self._func = func

  def set_value(self, *args, **kwargs):
    """set_value(*args, **kwargs)
    
    Set the value using the setter function. All arguments that are passed
    to this function, are passed to the setter. The value that is returned,
    is posted to all registered widgets as EVT_DATA_READY."""
    reply = self._func(*args, **kwargs)
    evt = DataReadyEvent(value = reply)
    evt.SetId(ID_DATA_REPLY)
    self.post_event(evt)


class Getter(Base):
  """Getter

  Get one value every given interval and propagate that value to the widgets
  that know how to handle it.
  """
  def __init__(self, func, default=None, interval = 1.0, **kwargs):
    super(Getter, self).__init__(**kwargs)
    self._func = func
    self._default = default

    self._continue = True
    self._thread = None

    self._value = None

    self.interval = interval

  def _run(self):
    while self._continue:
      val = self._get()
      evt = DataReadyEvent(value = val)
      self.post_event(evt)
      if self.interval:
        time.sleep(self.interval)
    self._continue = True

  def _get(self):
    self._value = self._func()
    return self._value

  def get_value(self):
    """get_value(): Returns the current value.

    If the object is currently active, this will return the last retrieved
    value, i.e. it will not call the getter method. If the object is not
    active, it will invoke the getter method to retrieve the most up-to-date
    value.
    """
    if self.is_acive():
      return self._value
    else:
      return self._get()

  def default(self):
    """default(): Returns the default value for this property.

    Depending on what the getter function relies on (e.g. a device that may be
    off-line), this method returns the default value, without invoking the
    getter method.
    """
    return self._default() if type(self._default) is types.FunctionType \
	else self._default

  def start(self):
    """start(): Start periodical invocation of the getter method.

    After calling this method, a thread will be created in which the getter
    method will be invoked every interval, and an event will be posted to all
    registered widgets.
    """
    self._thread = threading.Thread(target=self._run)
    self._thread.start()

  def is_active(self):
    """is_active(): Returns true if the object has been start()-ed."""
    return (self._thread != None)

  def stop(self):
    """stop(): Stop periodic invocation of the getter method."""
    if self._thread:
      self._continue = False
      self._thread.join()
      self._thread = None

  def reset(self):
    self.stop()
    self._value = None

  def __del__(self):
    self.stop()


class FullGetter(Getter):
  '''A FullGetter is a getter that can get multiple data columns and can
  store them in a history.
  '''
  def __init__(self, func, columns=None, history = 10000, **kwargs):
    super(FullGetter, self).__init__(func, **kwargs)

    if type(self._func) is not list:
      self._func = [self._func]

    if type(self._default) is not list:
      self._default = [self._default]

    self._num_columns = (len(self._func) if columns is None else
        sum(columns))

    self._data = numpy.zeros((0, self._num_columns))
    self._cur = 0
    self._value = None


    self.history = history

  def _get(self):
    val = []
    for g in self._func:
      val.append(g())
    val = reduce(list.__add__,(i if type(i) == list else [i]
      for i in val))
    if self._cur < self.history:
      self._data = numpy.append(self._data, [val], axis=0)
      self._cur += 1
    else:
      self._data = numpy.append(self._data[-self.history+1:], [val], axis=0)

      if self._cur > self.history:
	self._cur = self.history

    return numpy.array(val)

  def default(self):
    t = super(FullGetter, self).default()
    val = []
    for d in t:
      val.append(d() if type(d) is types.FunctionType else d)
    return reduce(list.__add__,(i if type(i) == list else [i]
      for i in val))

  def get_value(self):
    if self.is_active():
      return self._data[self._cur - 1]
    else:
      return self._get()

  def reset(self):
    super(FullGetter, self).reset()
    self._data = numpy.zeros((0, self._num_columns))
    self._cur = 0

  def get_values(self, size=None):
    if size:
      return self._data[-size:]
    else:
      return self._data


class TimedGetter(FullGetter):
  '''A TimedGetter is a FullGetter where the first column of the returned
  value array is the time in seconds since the TimedGetter was started.
  Optionally, an offset in seconds can be added.'''
  def __init__(self, func, default=None, offset=0, columns=None, **kwargs):
    if type(func) is not list: func = [func]
    func.insert(0, self._time)

    if type(default) is not list: default = [default]
    default.insert(0, offset)

    if columns is not None:
      columns.insert(0,1)

    super(TimedGetter, self).__init__(func=func, default=default,
        columns=columns, **kwargs)

    self.offset = offset
    self._t0 = None

  def _time(self):
    return time.time() - self._t0

  def start(self):
    if self._t0 == None:
      self._t0 = time.time() + self.offset
    super(TimedGetter, self).start()

  def reset(self):
    super(FullGetter, self).reset()
    self._t0 = None
