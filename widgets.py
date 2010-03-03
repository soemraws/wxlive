import wx

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

# vim: set shiftwidth=2 softtabstop=2 tabstop=8 expandtab: 
