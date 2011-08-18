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
    self._variable.value = self._convert_from(self.GetValue())
    self.SetBackgroundColour(wx.NamedColor('WHITE'))


class ToggleButton(wx.ToggleButton):
  def __init__(self, *args, **kwargs):
    pass

# vim: set filetype=python shiftwidth=2 softtabstop=2 tabstop=8 expandtab: 

