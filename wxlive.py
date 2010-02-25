import wx
import wx.lib.newevent
import threading
import time

# Event sent to widgets, containing the data that they can or may process.

VariableEvent, EVT_VARIABLE = wx.lib.newevent.NewEvent()

class Variable(object):
  '''
  Variable
  '''
  def __init__(self, variable_type, value, fget = None, fset = None,
      interval = 1.0, listeners = None, **kwargs):
    '''
    Variable(type, value, fget = None, fset = None,
      interval = 1.0)
    '''
    # Private - for internal use only
    self.__continue = False
    self.__thread = None

    # Protected - access only through methods
    self._id = wx.NewId()
    self._listeners = []
    self._value = None
    self._time = None
    self._time_offset = 0.0
    self._interval = float(interval)

    # Public - can be changed on the fly
    self.type = variable_type
    self.fget = fget
    self.fset = fset

    # Add the listeners
    if type(listeners) is list:
      for i in listeners:
        self.add_listener(i)
    else:
      self.add_listener(listeners)

    # Finally, set the initial value
    self.set_value(value)

  def get_id(self):
    return self._id

  id = property(fget = get_id)

  def get_interval(self):
    return self._interval

  def set_interval(self, value):
    if type(value) != float and type(value) != int:
      raise TypeError('Interval can only be a real number.')
    self._interval = float(value)

  interval = property(fget = get_interval, fset = set_interval)

  def get_time_offset(self):
    return self._time_offset

  def set_time_offset(self, value):
    if type(value) != float and type(value) != int:
      raise TypeError('Time offset can only be a real number.')
    self._time_offset = float(value)

  time_offset = property(fget = get_time_offset, fset = set_time_offset)

  def set_value(self, value):
    '''
    Set the value of the Variable.

    The value is first coerced to the type of the Variable. If the
    Variable has a set function defined, through fset, then the value is
    set using that function. If this function returns something other than
    None, this reply is emitted as the value of a VariableReplyEvent.
    After that, a VariableEvent is emitted with the new value of the
    Variable as its value.
    '''
    value = self.type(value)
    reply = None
    self._time = time.time() - self.time_offset
    if self.fset is not None:
      reply = self.fset(value)
    self._value = value
    evt = VariableEvent(time = self._time, value = self._value,
        reply = reply)
    evt.SetId(self._id)
    self.__post_event(evt)

  def get_value(self):
    '''
    Retrieve the value of the Variable. The value is updated first, by
    running update(), before returning, unless automatic updating is active
    (started using the start() method).
    '''
    if not self.is_active():
      self.update()
    return self._value

  def get_time_value_pair(self):
    '''
    Use get_value to obtain the current value of the LiveParameter, but return
    it as the second item in a tuple. The first item is the time (minus the
    time_offset) at which this value was updated.
    '''
    if not self.is_active():
      self.update()
    return (self._time, self._value)

  value = property(fget = get_value, fset = set_value,
      doc = 'The value of the Variable.')

  def update(self):
    '''
    Update the value of the Variable by running the get function and
    posting the VariableEvent, but without returning the value.

    Note that the value is updated even if automatic updating is already
    active.
    '''
    if self.fget is not None:
      value = self.type(self.fget())
      if value != self._value:
        self._time = time.time() - self.time_offset
        self._value = value
        evt = VariableEvent(time = self._time, value = self._value,
            reply = None)
        evt.SetId(self._id)
        self.__post_event(evt)

  def add_listener(self, listener):
    '''
    add_listener(listener)

    Adds a widget as a listener. The widget's on_live_variable_event will be
    bound to receive the wxlive.VariableEvent for this wxlive.Variable.

    If the widget does not have such an attribute, the event will not be
    bound, but the wxlive.Variable will still attempt to send events to the
    widget. Thus the programmer can Bind() to receive the
    wxlive.VariableEvent, as long as he Unbind()'s when required as well.
    '''
    if listener is not None:
      fchange = getattr(listener, 'on_live_variable_event', None)

      if fchange is not None:
        listener.Bind(EVT_VARIABLE, fchange, id = self._id)

      self._listeners.append(listener)

  def remove_listener(self, listener):
    '''
    remove_listener(listener)

    Removes a widget as a listener. The widget's on_live_variable_event will
    be unbound to recieve the wxlive.VariableEvent for this wxlive.Variable.
    Simply put, this method does the inverted of what add_listener() does, and
    the wxlive.Variable ceases to send wxlive.VariableEvent's to the widget.
    '''
    if listener is not None:
      fchange = getattr(listener, 'on_live_variable_event', None)

      if fchange is not None:
        listener.Unbind(EVT_VARIABLE, fchange, id = self._id)

      self._listeners.remove(listener)

  def start(self, interval = None):
    '''
    start(interval = None)

    Start automatic updating of the wxlive.Variable's value. The update()
    function is called with the given interval. The interval can be changed by
    setting the interval attribute of the wxlive.Variable.
    '''
    if interval is not None:
      self.interval = interval

    if not self.is_active():
      self.__continue = True
      self.__thread = threading.Thread(target=self.__run)
      self.__thread.start()

  def stop(self):
    '''
    stop()

    Stop automatic updating of the Variable's value.
    '''
    if self.__thread:
      self.__continue = False
      self.__thread.join()
      self.__thread = None

  def is_active(self):
    '''
    is_active()

    Returns True if automatic updating for this Variable has been started.
    '''
    return self.__thread is not None

  def reset_time_offset(self, value = None):
    '''
    reset_time_offset(value = None)

    Reset the time offset kept internally. By default, the current time (i.e.
    as returned by time.time()) is used.
    '''
    if value is None:
      self.time_offset = time.time()
    else:
      self.time_offset = value

  def __post_event(self, event):
    for w in self._listeners:
      try:
        wx.PostEvent(w, event)
      except (KeyboardInterrupt, SystemExit):
        raise
      except:
        self._listeners.remove(w)

  def __run(self):
    while self.__continue:
      self.update()
      if self._interval:
        time.sleep(self._interval)
    self.__thread = None

  def __eq__(self, other):
    return self.value == other

  def __ne__(self, other):
    return self.value != other

  def __lt__(self, other):
    return self.value < other

  def __le__(self, other):
    return self.value <= other

  def __gt__(self, other):
    return self.value > other

  def __ge__(self, other):
    return self.value >= other

  def __float__(self):
    return float(self.value)

  def __str__(self):
    return str(self.value)

  def __del__(self):
    self.stop()

  # wx insanity aliases
  GetId = get_id
  Id = id
  GetValue = get_value
  GetTimeValuePair = get_time_value_pair
  SetValue = set_value
  Value = value
  GetInterval = get_interval
  SetInterval = set_interval
  Interval = interval
  GetTimeOffset = get_time_offset
  SetTimeOffset = set_time_offset
  ResetTimeOffset = reset_time_offset
  TimeOffset = time_offset
  AddListener = add_listener
  RemoveListener = remove_listener
  Update = update
  Start = start
  Stop = stop
  IsActive = is_active


#### Functions

def make_listener(widget, live_variable_event_handler):
  '''
  make_listener(widget, live_variable_event_handler)

  Make any wx widget a listener widget, by setting an event handler for
  a wxlive.VariableEvent. The handler must receive one argument, the
  wxlive.VariableEvent. The handler will be set as an attribute
  on_live_variable_event to the widget, thereby duck typing it as a listener.

  The wxlive.VariableEvent has the following members that might be of
  interest:

  value     The recently updated value of the wxlive.Variable.
  time      The time when the wxlive.Variable was updated. This is the number
            of seconds since the epoch, minus the time offset of the
            wxlive.Variable.
  reply     The return value of the set function that the wxlive.Variable
            received in order to update the value.
  '''
  widget.on_live_variable_event = live_variable_event_handler


#### Widgets

class StaticText(wx.StaticText):
  def __init__(self, *args, **kwargs):
    format = '%s'
    if kwargs.has_key('format'):
      format = kwargs['format']
      del kwargs['format']
    wx.StaticText.__init__(self, *args, **kwargs)
    self.format = format
    self.on_live_variable_event = lambda x: self.SetLabel(self.format % x.value)

class TextCtrl(wx.TextCtrl):
  def __init__(self, *args, **kwargs):
    format = '%s'

    if kwargs.has_key('format'):
      format = kwargs['format']
      del kwargs['format']

    wx.TextCtrl.__init__(self, *args, **kwargs)

    self.format = format
    self.on_live_variable_event = lambda x: self.ChangeValue(self.format % x.value)
