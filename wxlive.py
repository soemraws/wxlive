import wx
from wx.lib.newevent import NewEvent
import threading
import time

# Event sent to widgets, containing the data that they can or may process.

VariableEvent, EVT_VARIABLE = NewEvent()

class Variable(object):
  '''
  A wxlive.Variable can send events to wx widgets that are listening, to
  inform them of a change in value. This allows the wx widgets to update their
  status according to the new value.

  The wxlive.Variable will send VariableEvents to wx widgets that are modified
  to become listeners (see make_listener), and are listening to this
  wxlive.Variable via the add_listener method.
  '''
  def __init__(self, variable_type, value, fget = None, fset = None,
      interval = 1.0, listeners = None, reply_is_new_value = False, **kwargs):
    '''
    wxlive.Variable(variable_type, value, fget = None, fset = None,
      interval = 1.0, listeners = None, reply_is_new_value = False)

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
    reply_is_new_value  Indicates that the reply of the set function is in
                        fact the new value for the variable.
    '''
    # Private - for internal use only
    self.__continue = False
    self.__thread = None
    self.__reply_is_new_value = reply_is_new_value

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
    '''
    get_id()

    Return the id for this wxlive.Variable. Each event that is sent by this
    wxlive.Variable will have this id set.
    '''
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

    The value must be of a type that is or can be coerced to a float.
    '''
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
    if self._reply and self.__reply_is_new_value:
      self._value = self.type(self._reply)
    else:
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

  def get_time(self):
    '''
    Retrieve the time of the last Variable update.
    '''
    return self._time

  time = property(fget = get_time)

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
      listener.Unbind(EVT_VARIABLE, listener, id = self._id)

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

  ## For comparisons
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

  def __int__(self):
    return int(self.value)

  def __str__(self):
    return str(self.value)

  def __del__(self):
    self.stop()


class VariableList(list):
  '''
  A list that contains wxlive.Variables and the possibility of running an
  update thread. This allows (near-)synchronisation of updating of multiple
  wxlive.Variables. Thus instead of start()-ing each wxlive.Variable
  separately, one can add all to a wxlive.VariableList, and start() the list.

  A wxlive.VariableList has an attribute called interval, which indicates the
  interval in seconds at which to update the wxlive.Variables. This attribute
  can be changed at any given time.

  CAVEAT: Once a wxlive.Variable is added to a wxlive.VariableList, it can
  still be updated separately, or even start()-ed on its own. This is not
  intended, but there is no explicit check to verify this.
  '''
  def __init__(self, interval = 1.0, *args, **kwargs):
    '''
    wxlive.VariableList(interval = 1.0)

    Construct a wxlive.VariableList with an updating interval in seconds
    (default: 1.0). Updating is not started yet.
    '''
    super(VariableList, self).__init__(*args, **kwargs)
    self.__thread = None
    self.__continue = False
    self._interval = float(interval)

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

    The value must be of a type that is or can be coerced to a float.
    '''
    self._interval = float(value)

  interval = property(fget = get_interval, fset = set_interval,
      doc = 'The interval at which to do automatic updating.')

  def append(self, item):
    '''
    append(item)

    Append an item, which must be an instance of a wxlive.Variable to the
    list. If the item was active (i.e. had been start()-ed) it will be
    stopped.
    '''
    if not isinstance(item, Variable):
      raise TypeError('Item must be instance of wxlive.Variable.')
    item.stop()
    super(VariableList, self).append(item)

  def prepend(self, item):
    '''
    prepend(item)

    Prepend an item, which must be an instance of a wxlive.Variable to the
    list. If the item was active (i.e. had been start()-ed) it will be
    stopped.
    '''
    if not isinstance(item, Variable):
      raise TypeError('Item must be instance of wxlive.Variable.')
    item.stop()
    super(VariableList, self).prepend(item)

  def start(self, interval = None):
    '''
    start(interval = None)

    Start updating of the wxlive.Variables in the wxlive.VariableList. If no
    interval in seconds is given, the interval attribute of the
    wxlive.VariableList is used.

    If the wxlive.VariableList was already start()-ed, this function does
    nothing else than potentially change the updating interval.
    '''
    if interval is not None:
      self.interval = float(interval)

    if not self.is_active():
      self.__continue = True
      self.__thread = threading.Thread(target=self.__run)
      self.__thread.start()

  def stop(self):
    '''
    stop()

    Stop updating the wxlive.Variables in the wxlive.VariableList.
    '''
    if self.__thread:
      self.__continue = False
      self.__thread.join()
      self.__thread = None

  def is_active(self):
    '''
    is_active()

    Predicate to see if the wxlive.VariableList() interval is start()-ed.
    '''
    return self.__thread is not None

  def __run(self):
    while self.__continue:
      for i in self:
        i.update()
      if self._interval:
        time.sleep(self._interval)

  def __del__(self):
    self.stop()


#### Functions

def make_listener(widget, live_variable_event_handler):
  '''
  make_listener(widget, live_variable_event_handler)

  Make any wx widget a listener widget, by setting an event handler for
  a wxlive.VariableEvent. The handler must receive one argument, the
  wxlive.VariableEvent. The handler will be set as an attribute
  on_live_variable_event to the widget, thereby duck typing it as a listener.

  Aside from the fact that the wxlive.VariableEvent has the id, as returned by
  the member function GetId(), of the wxlive.Variable that caused the event,
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

# vim: set shiftwidth=2 softtabstop=2 tabstop=8 expandtab: 

