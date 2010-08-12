#!/bin/env python

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

    #self.display = wxlive.StaticText(self.panel, wx.ID_ANY, '')
    self.display = wxlive.StripChart(self.panel, wx.ID_ANY, title='Demo stripchart')

    # Make a wxlive.Variable and add it to the wxlive.StripChart as a plot.
    self.sin = wxlive.Variable(float, None, fget=Sine, interval=0.5)
    self.display.add_plot(self.sin, 'ro-', label='sin(t/10)')

    # Make a second wxlive.Variable and add it to the wxlive.StripChart as a plot.
    self.cos = wxlive.Variable(float, None, fget=Cosine)
    self.display.add_plot(self.cos, 'b.--', label='cos(t/10)')

    self.display.set_bounds(0,30,-1,1)

    # Add the wxlive.StripChart as a listener to only one of the wxlive.Variables.
    # When this variable is started, the wxlive.StripChart will force updates
    # on the other wxlive.Variables that are added as plots.
    self.sin.add_listener(self.display)

    vbox = wx.BoxSizer(wx.VERTICAL)
    vbox.Add(self.display, 0, wx.ALL|wx.EXPAND, 5)
    self.panel.SetSizer(vbox)
    vbox.Fit(self)

    self.Bind(wx.EVT_CLOSE, self.on_close)

    # We only start the wxlive.Variable that has the wxlive.StripChart as a
    # listener. The other wxlive.Variable doesn't need to be started as the
    # wxlive.StripChart will request updates from it.
    self.sin.start()
    self.Show(True)

  def on_close(self, event):
    self.sin.stop()
    self.Destroy()


if __name__ == '__main__':
  app = wx.PySimpleApp()
  frame = DemoFrame(None, wx.ID_ANY, 'Demo')
  app.MainLoop()
