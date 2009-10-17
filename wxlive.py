#!/usr/bin/env python

import wx
import updater as p
import wx.lib.plot
from numpy import zeros

class LiveWidget(object):
  def __init__(self, widget, updater = None, column = None, **kwargs):
    self._updater = None
    self._column  = column
    self._updater_default = None
    self._widget = widget

    self._set_updater(updater)


  def _set_updater(self, updater):
    if self._updater:
      self._updater.unregister(self._widget)

    self._updater = updater

    if updater is not None:
      self._updater.register(self._widget)

    self._set_updater_default()

  def _set_updater_default(self):
    if self._updater and self.is_getter():
      self._updater_default = self._updater.default
    else:
      if self._column:
        self._updater_default = (lambda: [None] * (self._column+1))
      else:
        self._updater_default = (lambda: None)

  def is_setter(self):
    return hasattr(self._updater, 'set_value')

  def is_getter(self):
    return hasattr(self._updater, 'get_value')

  def __del__(self):
    del(self._updater)

  updater = property(fset=_set_updater)


class StaticText(wx.StaticText, LiveWidget):
  def __init__(self, updater = None, format = '%s', column = None, **kwargs):
    """
    StaticText(updater, format = '%s', column = None, **kwargs) -> wx.StaticText
    updater  -- The updater (updating getter)
    format   -- The format to use to convert the value of the getter into text
    column   -- If the getter returns an array, use only the specified column
    **kwargs -- Keyword arguments for a wx.StaticText
    """

    wx.StaticText.__init__(self,**kwargs)
    LiveWidget.__init__(self, widget=self, updater=updater, column=column, **kwargs)

    self._format = format

    self.Bind(p.EVT_DATA_READY, self.get)

    if self._updater is not None:
      self.default()

  def get(self, event):
    if self._column == None:
      self.SetLabel(self._format % event.value)
    else:
      self.SetLabel(self._format % event.value[self._column])

  def default(self, event = None):
    if self._column == None:
      self.SetLabel(self._format % self._updater_default())
    else:
      self.SetLabel(self._format % self._updater_default()[self._column])





class TextCtrl(wx.TextCtrl, LiveWidget):
  def __init__(self, updater = None, format = '%s', column = None, **kwargs):
    wx.TextCtrl.__init__(self, **kwargs)
    LiveWidget.__init__(self, widget=self, updater=updater, column=column, **kwargs)

    self._format = format

    if self.is_setter():
      self.Bind(wx.EVT_COMMAND_TEXT_ENTER, self.set)
    else:
      self.SetEditable(False)
      self.Bind(p.EVT_DATA_READY, self.get)

    if self._updater is not None:
      self.default()

  def get(self, event):
    if self._column:
      self.SetValue(self._format % event.value[self._column])
    else:
      self.SetValue(self._format % event.value)

  def default(self, event = None):
    if self._column == None:
      self.SetValue(self._format % self._updater_default())
    else:
      self.SetValue(self._format % self._updater_default()[self._column])

  def set(self, event = None):
    self._updater.set_value(self.GetValue())






class Choice(wx.Choice, LiveWidget):
  def __init__(self, updater = None, mapping = None, **kwargs):
    wx.Choice.__init__(self,**kwargs)
    LiveWidget.__init__(self, widget=self, updater=updater, **kwargs)

    if not mapping:
      self._mapping = range(len(kwargs['choices']))
    else:
      self._mapping = mapping

    wx.EVT_CHOICE(self, wx.ID_ANY, self.set)

  def set(self, event = None):
    self._updater.set_value(self._mapping[self.GetSelection()])




class CheckBox(wx.CheckBox, LiveWidget):
  def __init__(self, updater = None, **kwargs):
    wx.CheckBox.__init__(self, **kwargs)
    LiveWidget.__init__(self, widget=self, updater=updater, **kwargs)

    wx.EVT_CHECKBOX(self, wx.ID_ANY, self.set)

  def set(self, event = None):
    self._updater.set_value(self.GetValue())




class RadioButton(wx.RadioButton, LiveWidget):
  def __init__(self, updater = None, value = None, **kwargs):
    wx.RadioButton.__init__(self, **kwargs)
    LiveWidget.__init__(self, widget=self, updater=updater, **kwargs)
    self._value = value

    wx.EVT_RADIOBUTTON(self, wx.ID_ANY, self.set)

  def set(self, event = None):
    if self.GetValue():
      self._updater.set_value(self._value)


class PolyPoints(object):
  def __init__(self, updater = None, columns = (0,1), **kwargs):
    self._updater = updater
    self._columns = columns
    self._kwargs = kwargs
    self.visible = True

  def get_data(self, size=None):
    return self._updater.get_values(size)[0:,self._columns]

  def register(self, widget):
    self._updater.register(widget)

  def unregister(self, widget):
    self._updater.unregister(widget)


class PolyLine(PolyPoints):
  def __init__(self, updater = None, columns = (0,1), **kwargs):
    PolyPoints.__init__(self, updater, columns, **kwargs)


class PolyMarker(PolyPoints):
  def __init__(self, updater = None, columns = (0,1), **kwargs):
    PolyPoints.__init__(self, updater, columns, **kwargs)


class PlotGraphics(object):
  def __init__(self, polys = [], display_points = 100, **kwargs):
    self._polys = polys
    self._kwargs = kwargs
    self.display_points = display_points

    self.x_autoscale = True
    self.y_autoscale = True
    self.y_min = 0
    self.y_max = 10.0

  def canvas_kwargs(self):
    objects = []
    xmin = 9e99
    xmax = -9e99
    for x in self._polys:
      d = zeros((0,2))
      if x.visible:
        d = x.get_data(self.display_points)
      if self.x_autoscale and len(d) > 0:
        if xmin > d[0,0]:
          xmin = d[0,0]
        if xmax < d[-1,0]:
          xmax = d[-1,0]
      if isinstance(x, PolyLine):
        o = wx.lib.plot.PolyLine(d, **x._kwargs)
      elif isinstance(x, PolyMarker):
        o = wx.lib.plot.PolyMarker(d, **x._kwargs)
      else:
        raise TypeError, 'Unexpected type in plot'
      objects.append(o)

    retval = {'graphics': wx.lib.plot.PlotGraphics(objects, **self._kwargs)}

    if self.x_autoscale:
      if xmin == 9e99:
        xmin = 0.0
      if xmax == -9e99:
        xmax = 10.0
      retval['xAxis'] = (xmin, xmax)
    if not self.y_autoscale:
      retval['yAxis'] = (self.y_min, self.y_max)
    return retval

  def register(self, widget):
    for x in self._polys:
      x.register(widget)

  def unregister(self, widget):
    for x in self._polys:
      x.unregister(widget)

class PlotCanvas(wx.lib.plot.PlotCanvas):
  def __init__(self, graphics = None, popup=True, **kwargs):
    super(PlotCanvas, self).__init__(**kwargs)
    self._graphics = graphics
    graphics.register(self)

    self.Bind(p.EVT_DATA_READY, self.get)

    self._popup_ids = {}
    self._poly_menu_items = {}

    self.use_popup(popup)
    self.default()

  def get(self, event = None):
    self.Draw(**(self._graphics.canvas_kwargs()))

  def default(self, event = None):
    self.Draw(**(self._graphics.canvas_kwargs()))

  def _get_popup_id(self, key):
    if not key in self._popup_ids.keys():
      self._popup_ids[key] = wx.NewId()
    return self._popup_ids[key]

  def use_popup(self, popup=True):
    self._popup = popup

  def popup_menu(self):
    menu = wx.Menu()

    id = self._get_popup_id('Grid')
    self._item_grid = menu.AppendCheckItem(id, 'Grid')
    self._item_grid.Check(self.GetEnableGrid())
    wx.EVT_MENU(menu, id, self._on_grid)

    id = self._get_popup_id('Legend')
    self._item_legend = menu.AppendCheckItem(id, 'Legend')
    self._item_legend.Check(self.GetEnableLegend())
    wx.EVT_MENU(menu, id, self._on_legend)

    menu.AppendSeparator();

    scale = wx.Menu()

    id = self._get_popup_id('Autoscale X-axis')
    self._item_x_scale = scale.AppendCheckItem(id, 'Autoscale X-axis')
    self._item_x_scale.Check(self._graphics.x_autoscale)
    wx.EVT_MENU(scale, id, self._on_x_scale)

    id = self._get_popup_id('Autoscale Y-axis')
    self._item_y_scale = scale.AppendCheckItem(id, 'Autoscale Y-axis')
    self._item_y_scale.Check(self._graphics.y_autoscale)
    wx.EVT_MENU(scale, id, self._on_y_scale)

    menu.AppendMenu(-1, 'Scaling', scale)
    
    curves = wx.Menu()

    for x in self._graphics._polys:
      legend = x._kwargs['legend']
      id = self._get_popup_id(legend)
      item = curves.AppendCheckItem(id, legend)
      item.Check(x.visible)
      self._poly_menu_items[id] = (x,item)
      wx.EVT_MENU(curves, id, self._on_poly)

    menu.AppendMenu(-1, 'Curves', curves)

    return menu

  def OnMouseRightDown(self, event):
    if not self._popup:
      wx.lib.plot.PlotCanvas.OnMouseRightDown(self, event)
    else:
      menu = self.popup_menu()
      self.PopupMenu(menu, event.GetPosition())
      menu.Destroy()

  def _on_scale(self, event):
    pass

  def _on_grid(self, event):
    self.SetEnableGrid(self._item_grid.IsChecked())

  def _on_legend(self, event):
    self.SetEnableLegend(self._item_legend.IsChecked())

  def _on_poly(self, event):
    poly, item = self._poly_menu_items[event.GetId()]
    poly.visible = item.IsChecked()

  def _on_x_scale(self, event):
    self._graphics.x_autoscale = self._item_x_scale.IsChecked()

  def _on_y_scale(self, event):
    self._graphics.y_autoscale = self._item_y_scale.IsChecked()
