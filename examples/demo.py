import wx
import wxlive
from math import sin,cos
from time import time

def Sine():
  return sin(time()/10.0)

def Cosine():
  return cos(time()/10.0)

class DemoApp(wx.App):
  def __init__(self, *args, **kwargs):
    wx.App.__init__(self, *args, **kwargs)

class DemoFrame(wx.Frame):
  def __init__(self, *args, **kwargs):
    wx.Frame.__init__(self, *args, **kwargs)
    self.panel = wx.Panel(self)

    self.sin = wxlive.Variable(float, None, fget=Sine)
    self.cos = wxlive.Variable(float, None, fget=Cosine)
    #self.display = wxlive.StaticText(self.panel, wx.ID_ANY, '')
    self.display = wxlive.Graph(self.panel, wx.ID_ANY, x_offset=time())
    self.display.add_plot(self.sin.id, 1, (1,0,0))
    self.display.add_plot(self.cos.id, 1, (0,1,0))
    self.display.set_bounds(0,30,-1,1)
    self.sin.add_listener(self.display)
    self.cos.add_listener(self.display)

    vbox = wx.BoxSizer(wx.VERTICAL)
    vbox.Add(self.display, 0, wx.ALL|wx.EXPAND, 5)
    self.panel.SetSizer(vbox)
    vbox.Fit(self)

    self.Bind(wx.EVT_CLOSE, self.on_close)

    self.sin.start()
    self.cos.start()
    self.Show(True)

  def on_close(self, event):
    self.sin.stop()
    self.cos.stop()
    self.Destroy()


if __name__ == '__main__':
  app = wx.PySimpleApp()
  frame = DemoFrame(None, wx.ID_ANY, 'Demo')
  app.MainLoop()
