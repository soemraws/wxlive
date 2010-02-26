import wx
import wx.lib.newevent
import threading
import time

# Event sent to widgets, containing the data that they can or may process.

VariableEvent, EVT_VARIABLE = wx.lib.newevent.NewEvent()

class Variable(object):
  '''
  A wxlive.Variable allows for wx widgets that are listening to the variable,
  to update their state when the wxlive.Variable's value changes, by sending
  events.

  Simple usage
  ------------

  The value is set with the method set_value, or assigning to its value
  property:

    >>> var = wxlive.Variable(int, 5)
    >>> var.value
    5
    >>> var.value = 6
    >>> var.value
    6

  We can also define a set function:

    >>> def print_new_value(x):
    ...   print 'Value set to %d' % x
    ...
    >>> var = wxlive.Variable(int, 5, fset = print_new_value)
    Value set to 5
    >>> var.value = 6
    Value set to 6

  The value is retrieved with the method get_value, or querying its value
  property, as shown before. Similar to the set function, we can also define a
  get function:

    >>> import time
    >>> var = wxlive.Variable(float, time.time(), fget = time.time)
    >>> a = var.value ; time.sleep(2) ; b = var.value ; a == b
    False

  In the above example, it can be seen that retrieving the value of the
  wxlive.Variable will first update the value and then return that.

  This becomes more interesting, if e.g. the fset function is
  laser.set_frequency and the fget function is laser.get_frequency, where
  these functions set and return the current frequency of a laser system. If
  the laser is drifting a bit, it doesn't matter, since every time you
  evaluate the value of the wxlive.Variable, you actually get the most
  up-to-date frequency.

  It becomes more interesting, if you also have a wx.StaticText that displays
  the current frequency:

    >>> var = wxlive.Variable(float, laser.get_frequency(),
    ...   fget = laser.get_frequency, fset = laser.set_frequency)
    >>> frequency_display = wx.StaticText(parent, wx.ID_ANY)
    >>> make_listener(frequency_display, update_text)
    >>> var.add_listener(frequency_display)

  Now if the function update_text is defined as follows:

    >>> def update_text(event):
    ...   frequency_display.SetLabel('Current frequency: %f' % event.value)

  then the display will automatically be updated whenever the value of the
  wxlive.Variable is changed, either by assigning to it, or whenever it is
  evaluated.

  Updating the value automatically
  --------------------------------

  Each wxlive.Variable can actually update itself automatically, by running
  the get function (given with the keyword argument fget) in a thread. This
  can simply be done by using the start method, optionally with an interval
  which is 1.0 seconds by default.

  If a wxlive.Variable is automatically being updated (the thread has been
  started), the is_active method will return True. Each evaluation of the
  value will _not_ update the value, but instead just return the value as it
  was updated last by the thread. To force an update anyway even though
  automatic updating is active, use the get_value method with force=True.

  Automatic updating can be stopped using the stop method. The original
  behaviour is restored and every evaluation will update the value by running
  the function provided through the fget keyword.
  '''
  def __init__(self, variable_type, value, fget = None, fset = None,
      interval = 1.0, listeners = None, **kwargs):
    '''
    wxlive.Variable(type, value, fget = None, fset = None,
      interval = 1.0, listeners = None)

    Instantiate a wxlive.Variable of the given type, with the given value.

    Keyword arguments:
    variable_type  Type of the variable. In reality, this can be any type or
                   class name that also serves as a coercion function for that
                   type. E.g. int, float, str, list.
    value          The starting value for this variable. If this is not None,
                   then the fset function is called to set the variable. If it
                   is None, the initial value will be set to whatever the get
                   function (see fget) returns. This also means that any
                   listeners will immediately be informed of the changed
                   value.
    fget           A function that is called without arguments, and returns a
                   value that can be coerced into variable_type. See also
                   method update().
    fset           A function that is called with one argument, namely the new
                   value for the wxlive.Variable. See also method set_value().
    interval       The interval at which automatic updating of the value is
                   done. See method start().
    listeners      A single listener or a list of listeners. If this is not
                   None, the listeners will already be informed of the
                   wxlive.Variable's value upon its instantiation.
    '''
    # Private - for internal use only
    self.__continue = False
    self.__thread = None

    # Protected - access only through methods
    self._id = wx.NewId()
    self._listeners = []
    self._value = None
    self._time = None
    self._reply = None
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
    if value is None:
      self.get_value()
    else:
      self.set_value(value)

  def get_id(self):
    return self._id

  id = property(fget = get_id, doc = 'The id of this wxlive.Variable.')

  def get_interval(self):
    '''
    get_interval()

    Return the currently set interval at wich to do automatic updating.
    '''
    return self._interval

  def set_interval(self, value):
    '''
    set_interval(value)

    Set the interval at which to do automatic updating.

    The value must be an int or a float.
    '''
    if type(value) != float and type(value) != int:
      raise TypeError('Interval can only be a real number.')
    self._interval = float(value)

  interval = property(fget = get_interval, fset = set_interval,
      doc = 'The interval at which to do automatic updating.')

  def get_time_offset(self):
    '''
    get_time_offset()
    '''
    return self._time_offset

  def set_time_offset(self, value):
    '''
    set_time_offset(value)
    '''
    if type(value) != float and type(value) != int:
      raise TypeError('Time offset can only be a real number.')
    self._time_offset = float(value)

  time_offset = property(fget = get_time_offset, fset = set_time_offset)

  def set_value(self, value):
    '''
    set_value(value)

    Set the value of the wxlive.Variable.

    The value is first coerced to the type of the Variable. If the
    Variable has a set function defined, through fset, then the value is
    set using that function. If this function returns something other than
    None, this reply is emitted as the value of a VariableReplyEvent.
    After that, a VariableEvent is emitted with the new value of the
    Variable as its value.
    '''
    value = self.type(value)
    self._time = time.time() - self.time_offset
    if self.fset is not None:
      self._reply = self.fset(value)
    else:
      self._reply = None
    self._value = value
    self.__post_update_event()

  def get_value(self, force = False):
    '''
    Retrieve the value of the Variable. The value is updated first, by
    running update(), before returning, unless automatic updating is active
    (started using the start() method).
    '''
    if not self.is_active() or force:
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

  def get_reply(self):
    return self._reply

  reply = property(fget = get_reply)

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
        self.__post_update_event()

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
      evt = VariableEvent(time = self._time, value = self._value,
          reply = self._reply)
      evt.SetId(self._id)
      try:
        wx.PostEvent(listener, evt)
      except (KeyboardInterrupt, SystemExit):
        raise
      except:
        self._listeners.remove(listener)

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

  def __post_update_event(self):
    evt = VariableEvent(time = self._time, value = self._value,
        reply = self._reply)
    evt.SetId(self._id)
    for w in self._listeners:
      try:
        wx.PostEvent(w, evt)
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
  GetReply = get_reply
  Reply = reply
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
