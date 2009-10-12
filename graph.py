#!/usr/bin/env python
import wx
import wxlive
import updater
import time
import math

ID_START = 1
ID_GRID = 2
ID_LEGEND = 3
ID_QUIT = 99

def sine_of_time():
  return math.sin(time.time())

def cosine_of_time():
  return math.cos(time.time())

class MainWindow(wx.Frame):
  def __init__(self, *args, **kwargs):
    wx.Frame.__init__(self, *args, **kwargs)

    # The menu
    menubar = wx.MenuBar()

    # The menu
    file = wx.Menu()
    self.start_mnu = file.Append(ID_START, 'Start/Stop')
    file.Append(wx.ID_SEPARATOR)
    file.Append(ID_QUIT, '&Quit\tCtrl+Q')
    menubar.Append(file, '&File')
    view = wx.Menu()
    self.grid_mnu = view.AppendCheckItem(ID_GRID, 'Grid')
    self.legend_mnu = view.AppendCheckItem(ID_LEGEND, 'Legend')
    menubar.Append(view, '&View')
    self.SetMenuBar(menubar)

    self.Bind(wx.EVT_MENU, self.on_startstop, id=ID_START)
    self.Bind(wx.EVT_MENU, self.on_quit, id=ID_QUIT)
    self.Bind(wx.EVT_MENU, self.on_grid, id=ID_GRID)
    self.Bind(wx.EVT_MENU, self.on_legend, id=ID_LEGEND)

    # The sizer
    vbox = wx.BoxSizer(wx.VERTICAL)

    self.timegetter = updater.TimedGetter([cosine_of_time,sine_of_time],
	default = [0.0,0.0], interval = 0.1, history=10000)
    # You can also use a TextCtrl instead, which in getter mode will not be editable
    #timetxt = wxlive.TextCtrl(parent = self, id = wx.ID_ANY,
#	updater = self.timegetter, column=1, format='%0.2g')
    timetxt = wxlive.StaticText(parent = self, id = wx.ID_ANY,
	updater = self.timegetter, column=1, format='%0.2g')
    vbox.Add(timetxt, 0, 0, 10)

    polyline = wxlive.PolyLine(self.timegetter, columns=(0,1),
	legend='sin(t)', colour='red')
    polymarker = wxlive.PolyMarker(self.timegetter, columns=(0,2),
	legend='cos(t)', colour='blue')
    graph = wxlive.PlotGraphics(polys=[polyline,polymarker], xLabel='Time t [s]',
	yLabel='f(t)', title='Live graph')
    self.plot = wxlive.PlotCanvas(parent = self, id = wx.ID_ANY,
	graphics=graph)
    vbox.Add(self.plot, 1, wx.EXPAND, 10)

    self.SetSizer(vbox)

    self.statusbar = self.CreateStatusBar()

    self.Bind(wx.EVT_CLOSE, self.on_close)

    self.Show(True)

  def on_startstop(self, event):
    if self.timegetter.is_active():
      self.timegetter.stop()
    else:
      self.timegetter.start()

  def on_quit(self, event):
    self.Close()

  def on_grid(self, event):
    self.plot.SetEnableGrid(self.grid_mnu.IsChecked())

  def on_legend(self, event):
    self.plot.SetEnableLegend(self.legend_mnu.IsChecked())

  def on_close(self, event):
    self.timegetter.stop()
    del self.timegetter
    self.Destroy()

app = wx.PySimpleApp()
frame = MainWindow(None, wx.ID_ANY, 'wxLive test')
app.MainLoop()
