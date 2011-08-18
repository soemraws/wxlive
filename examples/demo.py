#!/bin/env python

import wx
import wxlive
from math import sin,cos
from time import time,sleep

import matplotlib
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

def Sine():
  return sin(time()/10.0)

def Cosine():
  return cos(time()/10.0)

class DemoFrame(wx.Frame):
  def __init__(self, *args, **kwargs):
    wx.Frame.__init__(self, *args, **kwargs)
    self.panel = wx.Panel(self)

    # Make a matplotlib figure as usual
    self.figure = matplotlib.figure.Figure((3,3), dpi=100)
    self.axes = self.figure.add_subplot(111)
    self.canvas = FigureCanvasWxAgg(self.panel, wx.ID_ANY, self.figure)

    # Make a wxlive.Variable
    self.sin = wxlive.Variable(float, None, fget=Sine, interval=0.5)

    # Make a second wxlive.Variable
    self.cos = wxlive.Variable(float, None, fget=Cosine, interval=0.2)

    # Here is where the magic comes in. We indicate that for the given axes
    # object, we want the self.cos variable to be the x variable for Variable
    # plots.
    wxlive.axes_set_time_as_x_variable(self.axes, 0.2, 'now')
    # For static plots, one can still give x and y lists or arrays. The
    # difference now is, that we can also plot a wxlive.Variable, which will
    # then be (one of) the y variable(s), like so:
    #self.axes.plot(self.sin, 'r-')

    # Even nicer is, that we can make a static and a variable plot...
    self.axes.plot([0,1,2,3],[0,.3,.6,.9],'b-', label='Static function')
    self.axes.plot(self.sin, 'r-', label='Variable', linewidth=2)
    self.axes.plot(self.cos, 'g--', label='Variable', linewidth=2)
    self.axes.legend()

    # ... or we can make them using a single plot call, like one of the
    # following. Keyword arguments then apply to all the plots, as specified
    # in the matplotlib documentation. The following four commands are
    # equivalent.
    #self.axes.plot([0,1,2,3] ,[0,.3,.6,.9],'b-', self.sin, 'r-', linewidth = 2)
    #self.axes.plot([0,.3,.6,.9],'b-', self.sin, 'r-', linewidth = 2)
    #self.axes.plot(self.sin, 'r-',[0,1,2,3],[0,.3,.6,.9],'b-',  linewidth = 2)
    #self.axes.plot(self.sin, 'r-',[0,.3,.6,.9],'b-',  linewidth = 2)

    self.axes.set_xbound(lower=-1, upper=30)
    self.axes.set_ybound(lower=-1, upper=1)

    vbox = wx.BoxSizer(wx.VERTICAL)
    vbox.Add(self.canvas, 0, wx.ALL|wx.EXPAND, 5)
    self.panel.SetSizer(vbox)
    vbox.Fit(self)

    self.Bind(wx.EVT_CLOSE, self.on_close)

    # We only start the wxlive.Variable that the canvas is listening to, i.e.
    # the one that was set as the x variable in the axes object. When the
    # value of this variable is updated, the canvas receives the new value,
    # and instructs the axes instance to update all its Variable plots
    # accordingly.
    self.Show(True)

  def on_close(self, event):
    self.axes.start()
    sleep(2)
    self.axes.stop()
    self.Destroy()

class DemoApp(wx.App):
  def __init__(self, *args, **kwargs):
    wx.App.__init__(self, *args, **kwargs)

  def OnInit(self):
    frame = DemoFrame(None, wx.ID_ANY, 'wxlive axes demo')
    frame.Show(True)
    self.SetTopWindow(frame)
    return True

if __name__ == '__main__':
  app = DemoApp()
  app.MainLoop()
