#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
from ..utils import stopifnot, as_dict, json_cache

class KeyFrame:
  
  def __init__(self, name, time, value, dtype='continuous',
    target = ".material.color"):
    self.name = name
    self.cached = False
    self._cache_path = None
    self.target = target
    self._dtype = 'continuous'
    self._time = None
    self._values = None
    self._levels = None
    
    if not isinstance(value, list):
      value = [value]
    if not isinstance(time, list):
      time = [time]
    
    stopifnot(len(value) == len(time), 
      msg='time and value should equal in length')
    
    # raise error if time is not numeric
    # I don't want to do extra checks as you could break the 
    # system whatever you want, as long as it works
    time[0] + 1
    
    if dtype == 'continuous':
      self._dtype='continuous'
      sel = [False if x is math.nan else True for x in value]
      self._time = [y for x, y in zip(sel, time) if x]
      self._values = [y for x, y in zip(sel, value) if x]
    else:
      self._dtype='discrete'
      # TODO: check if this is ordered
      if hasattr(value, '_levels'):
        self._levels = getattr(value, '_levels')
      else:
        # generate levels
        self._levels = list(set(value))
      # map value
      new_v = []
      new_t = []
      for t, v in zip(time, value):
        if v in self._levels:
          new_v.append(v)
          new_t.append(t)
      self._values = new_v
      self._time = new_t
    
    
  
  def to_dict(self):
    return as_dict({
      'name' : self.name,
      'time' : self._time,
      'value' : self._values,
      'data_type': self._dtype,
      'target' : self.target,
      'cached' : self.cached,
      'cache_path' : self._cache_path
    })
  
  def use_cache(self, path, name):
    if self.cached:
      return None
    json_cache(path=path, data={
      name : self.to_dict()
    })
    self._cache_path = path
    self.cached = True
    if self.is_continuous:
      self._values = [min(self._values), max(self._values)]
    else:
      self._values = self._levels
    
  
  @property
  def is_continuous(self):
    return self._dtype == 'continuous'
  
  @property
  def time_range(self):
    if self._time is None or len(self._time) == 0:
      return [0,0]
    return [min(self._time), max(self._time)]
  
  @property
  def value_range(self):
    if self.is_continuous:
      return [min(self._values), max(self._values)]
    return None
  
  @property
  def value_names(self):
    if self.is_continuous:
      return None
    return self._levels


class KeyFrame2(KeyFrame):
  def __init__(self, name, time, value, dtype = "continuous", 
    target = ".geometry.attributes.color.array"):
    if dtype == 'continuous':
      # Please make sure vakue and time are valid, no checks here
      self._dtype = 'continuous'
    else:
      self._dtype = 'discrete'
      # If is factor, then do not remake factor as we need to keep the levels
      if hasattr(value, '_levels'):
        self._levels = getattr(value, '_levels')
      else:
        # generate levels
        self._levels = list(set(value))
    
    stopifnot(len(value) > 0, 
      msg='KeyFrame2 value cannot have 0 length')
    stopifnot(len(value) == len(time),
      msg='KeyFrame2 value and time must have equal length')
    time[0] + 1.0
    
    self.name = name
    self.target = target
    self._time = time
    self._values = value
    pass
  

class ColorMap:
  
  def __init__(self, name, geoms = [], symmetric = 0, alias = None):
    self.name = name
    self.alias = None
    self.value_type = 'continuous'
    self.time_range = [0,1]
    self.value_range = [-1,1]
    self.hard_range = None
    self.value_names = []
    self.n_colors = 64
    self.colors = ["#000080", "#E2E2E2", "#FF0000"]
    
    if alias is not None:
      self.alias = alias
    
    # get time range
    time_range = []
    for g in geoms:
      rg = g.animation_time_range( name )
      if isinstance(rg, list):
        time_range.extend( rg )
    if len(time_range) == 0:
      time_range = [0, 1]
    elif len(time_range) == 1:
      time_range = [time_range[0] - 1, time_range[0]]
    self.time_range = [min(time_range), max(time_range)]
    
    # get value range
    value_range = []
    for g in geoms:
      vg = g.animation_value_range( name )
      if isinstance(vg, list):
        value_range.extend( vg )
    if len(value_range) == 0:
      value_range = [-1, 1]
    elif len(value_range) == 1:
      value_range = [value_range[0] - 1, value_range[0]]
    self.value_range = [min(value_range), max(value_range)]
    
    # get value names
    value_names = []
    for g in geoms:
      vn = g.animation_value_names( name )
      if isinstance(vn, list):
        for n in vn:
          if not n in value_names:
            value_names.append( n )
    self.value_names = value_names
    
    if len(self.value_names) > 0:
      self.value_type = 'discrete'
      self.colors = ["#FFA500", "#1874CD", "#006400", 
        "#FF4500", "#A52A2A", "#7D26CD"]
    else:
      self.value_type = 'continuous'
      self.colors = ["#000080", "#E2E2E2", "#FF0000"]
      
    self.set_colors()
  
  def set_colors(self, colors = []):
    if len(colors) <= 1:
      colors = self.colors
    col_copy = colors.copy()
    
    if self.value_type == 'continuous':
      self.colors = col_copy
      self.n_colors = max(64, self.n_colors)
    else: 
      # discrete
      self.n_colors = len( self.value_names )
      if self.n_colors > len( col_copy ):
        # expand color
        self.colors = color_interpolate_hex(col_copy, self.n_colors)
      else:
        self.colors = col_copy[:self.n_colors]
  
  def to_dict(self):
    ncols = math.log2(self.n_colors)
    ncols = math.ceil(ncols)
    ncols = int(math.pow(2, ncols))
    ncols = max(16, ncols)
    colors = color_interpolate_hex(self.colors, ncols)
    if self.value_type == 'continuous':
      step = (self.value_range[1] - self.value_range[0]) / ncols
      color_keys = [self.value_range[0] + step * i for i in range(ncols)]
    else:
      color_keys = [i+1 for i in range(ncols)]
    return {
      'name'          : self.name,
      'time_range'    : self.time_range,
      'value_range'   : self.value_range,
      'value_names'   : self.value_names,
      'value_type'    : self.value_type,
      'color_keys'    : color_keys,
      'color_vals'    : [c.replace('#', '0x') for c in colors],
      # Mainly used to indicate how many levels
      'color_levels'  : self.n_colors,
      'hard_range'    : self.hard_range,
      'alias'         : self.alias
    }

def color_hex2rgb( h, mx=255 ):
  h = h.lstrip('#')
  if mx == 255:
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
  else:
    return tuple(int(h[i:i+2], 16) / 255 * mx for i in (0, 2, 4))


def color_rgb2hex( r, g, b, mx = 255 ):
  return '#%02x%02x%02x' % (
    math.floor(r * 255 / mx), 
    math.floor(g * 255 / mx), 
    math.floor(b * 255 / mx)
  )

def color_interpolate_hex( cols, n ):
  step = (len(cols) - 2.0) / (n - 1.0)
  rgbs = [color_hex2rgb(h) for h in cols]
  re = []
  for i in range(n):
    v = step * i
    a = math.floor(v)
    b = math.ceil(v)
    if b + 1 >= len(cols):
      b = len(cols) - 1
    r1,g1,b1 = rgbs[a]
    r2,g2,b2 = rgbs[b]
    r3 = (v - a) * r2 + (b - v) * r1
    g3 = (v - a) * g2 + (b - v) * g1
    b3 = (v - a) * b2 + (b - v) * b1
    re.append( color_rgb2hex(r3,g3,b3) )
  return re

