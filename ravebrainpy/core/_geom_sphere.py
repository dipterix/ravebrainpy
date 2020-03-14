#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
from ..utils import stopifnot, as_dict
from ._keyframe import KeyFrame
from ._geom_abs import AbstractGeom

class SphereGeom(AbstractGeom):
  
  
  def __init__(self, name, position = [0,0,0], radius = 5, **kwargs):
    super().__init__(name=name, position=position, **kwargs)
    self.radius = radius
    self.width_segments = kwargs.get('width_segments', 10)
    self.height_segments = kwargs.get('height_segments', 6)
    self.geom_type = 'sphere'
    
    if 'value' in kwargs:
      self.set_value(
        value = kwargs.get('value', None),
        time_stamp = kwargs.get('time_stamp', None),
        name = kwargs.get('value_name', 'default')
      )
    
    
  def to_dict(self):
    re = super().to_dict()
    re['radius'] = self.radius
    re['width_segments'] = self.width_segments
    re['height_segments'] = self.height_segments
    return re
  
class ElectrodeGeom(SphereGeom):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.is_surface_electrode = True
    self.use_template = False
    self.surface_type = 'pial'
    self.hemisphere = None
    self.vertex_number = -1
    self.MNI305_position = [0,0,0]
  
  def to_dict(self):
    re = super().to_dict()
    re['is_electrode'] = True
    re['is_surface_electrode'] = self.is_surface_electrode
    re['use_template'] = self.use_template
    re['surface_type'] = self.surface_type
    re['hemisphere'] = self.hemisphere
    re['vertex_number'] = self.vertex_number
    re['MNI305_position'] = self.MNI305_position
    re['sub_cortical'] = not self.is_surface_electrode
    re['search_geoms'] = self.hemisphere
    return re
  
