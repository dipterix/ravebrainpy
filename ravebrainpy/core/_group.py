#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import os
from ..utils import *
MAT4IDENTITY = (1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,)

class GeomGroup(object):
  '''
  Geometry group that contains multiple geometries with their shared 
  data
  '''
  
  def __str__(self):
    template = '''Geometry group <%s>
Meta data:
  Parent object : %s
  Subject       : %s
  Data path     : %s
Parameters:
  Layer         : %s
  Position      : %.2f, %.2f, %.2f,
  Transform     : 
    %.2f, %.2f, %.2f, %.2f, 
    %.2f, %.2f, %.2f, %.2f, 
    %.2f, %.2f, %.2f, %.2f, 
    %.2f, %.2f, %.2f, %.2f
  '''
    args = [
      self.name, self.parent_group, self.subject_code, self.cache_path,
      self.layer, self.position[0], self.position[1], self.position[2]
    ]
    args.extend(list(self._trans_mat))
    return template % tuple(args)
  
  def __init__(self, name, layer = [0], position = [0,0,0], 
    cache_path=None, parent = None ):
    self.name = name
    self.parent_group = None
    self.subject_code = None
    
    self.layer = set()
    self.position = [0,0,0]
    
    self.group_data = {}
    self._trans_mat = MAT4IDENTITY
    self.disable_trans_mat = False
    
    self.cached_items = []
    self.cache_env = {}
    self.cache_path = None
    
    stopifnot(all([l in range(14) for l in layer]), msg = '''\
    layer must be integer from 0-13:
      0  for main camera-only,
      1  for all cameras,
      13 is invisible''')
      
    self.layer.update(layer)
    
    stopifnot(len(position) == 3, msg="position must have length of 3")
    self.position = list(position)
    if cache_path is None:
      cache_path = tempfile()
    self.cache_path = cache_path
    
    # assign parent_group
    if parent is not None:
      if not isinstance(parent, str):
        parent = parent.name
      self.parent_group = parent
  
  def cache_name( self ):
    '''
    Generate legal file name or internal name
    
    Returns
    -------
    A safe name that can be used as file name
    '''
    
    return re.sub(
      pattern = r'[^a-zA-Z0-9]', 
      repl = '_', 
      string = self.name
    )
  
  def set_transform( self, m11, m12, m13, m14, m21, m22, m23, m24,
                           m31, m32, m33, m34, m41, m42, m43, m44 ):
    self._trans_mat = ( m11, m12, m13, m14, m21, m22, m23, m24,
                        m31, m32, m33, m34, m41, m42, m43, m44, )
    return self._trans_mat 
  
  def set_group_data( self, name, value, is_cached=False, 
    cache_if_not_exists=False ):
    
    # case: cache is missing
    if cache_if_not_exists and not is_cached:
      # create cache path
      path = os.path.join( self.cache_path, re.sub(
        pattern = r'[^a-zA-Z0-9.]', 
        repl = '_', 
        string = name
      ))
      # We never override cache. 
      if not os.path.exists( path ):
        value = json_cache( path, { name : value })
        is_cached = True
      
    self.group_data[name] = value
    if is_cached:
      self.cached_items.append( name )
    return value
    
  
  def get_data(self, key, force_reload = False, ifnotfound = None):
    if key in self.group_data:
      re = self.group_data.get(key, ifnotfound)
      
      if type(re) is dict and re.get('is_cache', False) == True:
        # this is a cache, load from cache!
        if not force_reload and key in self.cache_env:
          return self.cache_env.get(key, ifnotfound)
        
        
        # load cache
        print('Loading from cache')
        d = from_json(from_file = re['absolute_path'])
        
        for k, v in d.items():
          self.cache_env[k] = v
        return self.cache_env.get(key, ifnotfound)
      
      return re
      
    return ifnotfound
  
  def to_dict(self):
    return as_dict({
      'name'          : self.name,
      'layer'         : self.layer,
      'position'      : self.position,
      'group_data'    : self.group_data,
      'trans_mat'     : self._trans_mat,
      'cached_items'  : self.cached_items,
      'cache_name'    : self.cache_name(),
      'disable_trans_mat' : self.disable_trans_mat,
      'parent_group'  : self.parent_group,
      'subject_code'  : self.subject_code
    })

