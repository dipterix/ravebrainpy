#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from ..utils import stopifnot, as_dict, json_cache, normalize_path
from ._keyframe import KeyFrame2 
from ._geom_abs import AbstractGeom

class FreeGeom(AbstractGeom):
  def __init__(self, name, group, vertex=None, face=None,
    position = [0,0,0], cache_file=None, **kwargs):
    
    # Initialization
    super().__init__(name=name, position = position, **kwargs)
    
    self.group = group
    self.cache_file = None
    self.geom_type = 'free'
    self.value = None
    self.clickable = False
    self.hemisphere = None
    self.surface_type = None
    
    # Set cache_file
    if cache_file is not None:
      cache_exists = os.path.exists(cache_file)
      if cache_exists:
        cache_file = normalize_path(cache_file)
      self.cache_file = cache_file
      # cache_file = '/Users/beauchamplab/rave_data/data_dir/demo/YAB/fs/RAVE/YAB_fs_lh_pial.json'
      if vertex is None or face is None:
        # this means we relies on cache_file, it must exists
        stopifnot(cache_exists, 
          msg="Either %s must exist or %s are provided" % (
            'cache_file', '(vertex, face)'
          ))
        
        re = {
          'path' : cache_file,
          'absolute_path' : cache_file,
          'file_name' : os.path.basename(cache_file),
          'is_new_cache' : False,
          'is_cache' : True
        }
    if vertex is not None and face is not None:
      for v in vertex:
        stopifnot(len(v) == 3, msg = '''
Each element of `vertex` must be a list of 3, for example:
vertex=[[1,2,3], [1,3,4], ...]''')
      
      for f in face:
        stopifnot(len(f) == 3, msg = '''
Each element of `face` must be a list of 3, for example:
face=[[0,1,2], [0,1,3], ...]''')
      
      if cache_file is not None:
        data = {
          'free_vertices_%s' % name : vertex, 
          'free_faces_%s' % name : face
        }
        # Do NOT recache if exists
        re = json_cache(path = cache_file, data = data)
        self.group.set_group_data(
          'free_vertices_%s' % name, value = re, is_cached = True )
        self.group.set_group_data(
          'free_faces_%s' % name, value = re, is_cached = True )
      else:
        self.group.set_group_data('free_vertices_%s' % name, value = vertex)
        self.group.set_group_data('free_faces_%s' % name, value = face)
    else:
      re = {
        'path' : cache_file,
        'absolute_path' : normalize_path( cache_file ),
        'file_name' : os.path.basename( cache_file ),
        'is_new_cache' : False,
        'is_cache' : True
      }
      self.group.set_group_data(
        'free_vertices_%s' % name, value = re, is_cached = True )
      self.group.set_group_data(
        'free_faces_%s' % name, value = re, is_cached = True )
    pass
  
  def set_value(self, value = None, time_stamp=0, name='Value',
    target=".geometry.attributes.color.array", **kwargs):
    
    stopifnot(self.cache_file is not None, 
      msg='Must enable cache_file to set values for a Free geometry')
    
    name = name.strip()
    stopifnot(name != '[None]', 
    msg = '''Free geometry cannot have varaible name "[None]". 
    It's reserved''')
    
    # check length of value
    if value is None or len(value) == 0:
      # remove keyframe
      return self.keyframes.pop(name, None)
    
    kf = KeyFrame2(name=name, value=value, time=time_stamp,
      dtype = 'discrete' if isinstance(value[0], str) else 'continuous',
      target = target)
    
    cf = self.cache_file.rstrip('.json') + '__' + name + '.json'
    dname = 'free_vertex_colors_%s_%s' % (name, self.name)
    
    kf.use_cache( path = cf, name = dname )
    re = {
      'path' : cf,
      'absolute_path' : normalize_path( cf ),
      'file_name' : os.path.basename( cf ),
      'is_new_cache' : False,
      'is_cache' : True
    }
    self.keyframes[name] = kf
    self.group.set_group_data(dname, value = re, is_cached = True)
    return kf
  
  def to_dict(self):
    re = super().to_dict()
    re['hemisphere'] = self.hemisphere
    re['surface_type'] = self.surface_type
    return re
