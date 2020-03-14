#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from ..utils import stopifnot, json_cache, rand_string, tempfile
from ..utils import normalize_path
from ._geom_abs import AbstractGeom
from ._keyframe import KeyFrame2
from ._group import GeomGroup

def _get_dim(cube):
  return [len(cube), len(cube[0]), len(cube[0][0])]

def _spread_cube(cube):
  import numpy as np
  return np.array(cube).flatten('F').tolist()
  

class DataCubeGeom(AbstractGeom):
  def __init__(self, name, group, 
    value=None, dim = None, half_size = [128,128,128], position=[0,0,0],
    cache_file=None, layer = [13], digest=True, **kwargs):
    super().__init__(name=name,position=position,layer=layer,**kwargs)
    
    if group is None or not isinstance(group, GeomGroup):
      group = GeomGroup(name='default' + rand_string(5))
    self.group = group
    
    if cache_file is not None:
      if cache_file == True:
        cache_file = tempfile(ext = '.json')
      
      # case 1: only use cache file
      if value is None:
        stopifnot(os.path.exists(cache_file), 
          msg = 'cache_file does not exist and value is missing')
        cache_file = normalize_path(cache_file)
        re = {
          'path' : cache_file,
          'absolute_path' : cache_file,
          'file_name' : os.path.basename(cache_file),
          'is_new_cache' : False,
          'is_cache' : True
        }
      else:
        # case 2: use cache file and data is provided
        # still check data
        if dim is None or len(dim) != 3:
          dim = _get_dim(value)
        value = _spread_cube(value)
        data = {
          'datacube_value_%s' % name : value,
          'datacube_dim_%s' % name : dim,
          'datacube_half_size_%s' % name : half_size,
        }
        
        re = json_cache(path = cache_file, data=data, digest=digest)
      self.group.set_group_data(
        name = 'datacube_value_%s' % name,
        value = re, is_cached = True
      )
      self.group.set_group_data(
        name = 'datacube_dim_%s' % name,
        value = re, is_cached = True
      )
      self.group.set_group_data(
        name = 'datacube_half_size_%s' % name,
        value = re, is_cached = True
      )
    else:
      if dim is None or len(dim) != 3:
        dim = _get_dim(value)
      value = _spread_cube(value)
      self.group.set_group_data(
        name = 'datacube_value_%s' % name,
        value = value, is_cached = True
      )
      self.group.set_group_data(
        name = 'datacube_dim_%s' % name,
        value = dim, is_cached = True
      )
      self.group.set_group_data(
        name = 'datacube_half_size_%s' % name,
        value = half_size, is_cached = True
      )
    
    self.geom_type = 'datacube'
    self.clickable = False
  
  def set_value(self):
    print('set_value has not been implemented yet')
    pass
  


  
