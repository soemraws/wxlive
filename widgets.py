import wx

class StaticText(wx.StaticText):
  def __init__(self, *args, **kwargs):
    if kwargs.has_key('convert_to'):
      self._convert_to = kwargs['convert_to']
      del kwargs['convert_to']
    else:
      self._convert_to = lambda x: x

    wx.StaticText.__init__(self, *args, **kwargs)

  def on_live_variable_event(self, evt):
    self.SetLabel(self._convert_to(evt.value))


class TextCtrl(wx.TextCtrl):
  def __init__(self, *args, **kwargs):
    if kwargs.has_key('convert_to'):
      self._convert_to = kwargs['convert_to']
      del kwargs['convert_to']
    else:
      self._convert_to = lambda x: x

    wx.TextCtrl.__init__(self, *args, **kwargs)

  def on_live_variable_event(self, evt):
    self.ChangeValue(self._convert_to(evt.value))


class TextEntry(TextCtrl):
  def __init__(self, *args, **kwargs):
    if kwargs.has_key('convert_from'):
      self._convert_from = kwargs['convert_from']
      del kwargs['convert_from']
    else:
      self._convert_from = lambda x: x

#    if kwargs.has_key('style'):
#      kwargs['style'] = kwargs['style'] | wx.TE_PROCESS_ENTER
#    else:
#      kwargs['style'] = wx.TE_PROCESS_ENTER

    TextCtrl.__init__(self, *args, **kwargs)

    self._variable = None

  def set_variable(self, variable):
    self._variable = variable

    if self._variable is None:
      self.Unbind(wx.EVT_TEXT_ENTER, self)
      self.Unbind(wx.EVT_TEXT, self)
    else:
      self.Bind(wx.EVT_TEXT_ENTER, self.on_press_enter)
      self.Bind(wx.EVT_TEXT, self.on_modify_text)

  def on_modify_text(self, event):
    self.SetBackgroundColour(wx.NamedColor('PINK'))

  def on_press_enter(self, event):
    self._variable.set_value(self._convert_from(self.GetValue()), self)
    self.SetBackgroundColour(wx.NamedColor('WHITE'))


class Slider(wx.Slider):
  def __init__(self, *args, **kwargs):
    if kwargs.has_key('convert_from'):
      self._convert_from = kwargs['convert_from']
      del kwargs['convert_from']
    else:
      self._convert_from = lambda x: x
    if kwargs.has_key('convert_to'):
      self._convert_from = kwargs['convert_to']
      del kwargs['convert_to']
    else:
      self._convert_from = lambda x: x

    wx.Slider.__init__(self, *args, **kwargs)
      
  def set_variable(self, variable):
    self._variable = variable

    if self._variable is None:
      self.Unbind(wx.EVT_SCROLL, self)
    else:
      self.Bind(wx.EVT_SCROLL, self.on_scroll)
      
  def on_live_variable_event(self, evt):
    self.SetValue(self._convert_to(evt.value))

  def on_scroll(self, evt):
    self._variable.set_value(self._convert_from(self.GetValue()), self)

class ToggleButton(wx.ToggleButton):
  def __init__(self, *args, **kwargs):
    pass

# vim: set filetype=python shiftwidth=2 softtabstop=2 tabstop=8 expandtab: 

