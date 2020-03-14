#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
from ..utils import stopifnot, as_dict
from ._keyframe import KeyFrame
class AbstractGeom:
  
  def __init__(self, name, position = [0,0,0], 
                group = None, layer = [0] ):
    self.geom_type = 'abstract'
    self.time_stamp = None
    self.value = None
    self.keyframes = {}
    self.position = [0,0,0]
    self.group = None
    self.clickable = True
    self.layer = set()
    self.use_cache = False
    self.custom_info = ''
    self.subject_code = None
    self.name = name
    
    self.set_position(position)
    self.group = group
    stopifnot(all([l in range(14) for l in layer]), msg='''\
    layer must be integer from 0-13
      0: main camera-only
      1: all cameras
      13: invisible''')
    self.layer.update(layer)
    
  
  def set_position(self, *args):
    pos = []
    for item in args:
      if isinstance(item, (list, tuple, )):
        for i in item:
          pos.append(i)
      else:
        pos.append(item)
    stopifnot(len(pos) == 3, msg = "position must have length 3")
    self.position = pos
  
  def set_value(self, name, value=None, time_stamp=None, 
    target = ".material.color", *args, **kwargs):
    if value is None:
      value=[]
    if not isinstance(value, list):
      value = [value]
    # check length
    if len(value) > 1:
      stopifnot(len(value) == len(time_stamp),
        msg = 'Please specify time_stamp for each value')
    else:
      if len(value) == 0:
        # remove keyframe
        return self.keyframes.pop(name, None)
      elif time_stamp is None or len(time_stamp) != 1:
        time_stamp = 0
    
    if not isinstance(time_stamp, list):
      time_stamp = [time_stamp]
    
    # Check NA in value and remove
    sel = [True if x is math.nan else False for x in value]
    n_nans = sum(sel)
    if n_nans == len(value):
      return self.keyframes.pop(name, None)
    
    if n_nans > 0:
      time_stamp = [y for x,y in zip(sel, time_stamp) if not x]
      value = [y for x,y in zip(sel, value) if not x]
    else:
      time_stamp = time_stamp.copy()
      value = value.copy()
    
    # Create new keyfrems
    kf = KeyFrame(name=name, value=value, time=time_stamp, 
      dtype='discrete' if type(value[0]) is str else 'continuous',
      target=target)
    
    self.keyframes[name] = kf
  
  
  def to_dict(self):
    group_info = {}
    subject_code = self.subject_code
    if self.group is not None:
      group_info = {
        'group_name'      : self.group.name,
        'group_layer'     : self.group.layer,
        'group_position'  : self.group.position
      }
      if subject_code is None:
        subject_code = self.group.subject_code
    
    kfs = {}
    for nm, kf in self.keyframes.items():
      kfs[nm] = kf.to_dict()
    
    return as_dict({
      'name'            : self.name,
      'type'            : self.geom_type,
      'time_stamp'      : self.time_stamp,
      'position'        : self.position,
      'value'           : self.value,
      'clickable'       : self.clickable,
      'layer'           : self.layer,
      'group'           : group_info,
      'use_cache'       : self.use_cache,
      'custom_info'     : self.custom_info,
      'subject_code'    : subject_code,
      'keyframes'       : kfs
    })
  
  def get_data(self, key='value', force_reload=False, ifnotfound=None):
    # TODO: check whether we can remove this
    # if hasattr(self, key):
    #   return getattr(self, key)
    if key in self.keyframes:
      return self.keyframes[key]._values
    if self.group is not None and key in self.group.group_data:
      return self.group.get_data(key, force_reload=force_reload, 
        ifnotfound=ifnotfound)
    return ifnotfound
    
  
  def animation_time_range(self, ani_name):
    if ani_name in self.keyframes:
      return self.keyframes[ani_name].time_range
    return None
  
  def animation_value_range(self, ani_name):
    if ani_name in self.keyframes:
      kf = self.keyframes[ani_name]
      if kf.is_continuous:
        return kf.value_range
    return None
  
  def animation_value_names(self, ani_name):
    if ani_name in self.keyframes:
      kf = self.keyframes[ani_name]
      if not kf.is_continuous:
        return kf.value_names
    return None
  
  @property
  def animation_types(self):
    return list(self.keyframes.keys())

