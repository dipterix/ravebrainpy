#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import TestCase
import math
import string

import ravebrainpy.core as c
import ravebrainpy.utils as pu

if False:
  self = TestCase()
  # self.gp = c.GeomGroup(name='test*group', layer=[0,1])
  # json_cache = pu.json_cache
  # gp = self.gp
  kf = c.KeyFrame(name='testkf', value=1, time = 0)

class TestGroups(TestCase):
  gp = None
  def ensure(self):
    if self.gp is None:
      self.gp = c.GeomGroup(name='test*group', layer=[0,1])
      pu.unlink(self.gp.cache_path + '/dset')
    return self.gp
  
  def test_init_group(self):
    gp = self.ensure()
    self.assertTrue(isinstance(gp.__str__(), str))
  
  def test_transmat(self):
    gp = self.ensure()
    gp.set_transform(1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6)
    self.assertEqual(len(gp._trans_mat), 16)
  
  def test_name(self):
    gp = self.ensure()
    self.assertEqual(gp.cache_name(), 'test_group')
    
  def test_setget_data(self):
    gp = self.ensure()
    # no error
    gp.set_group_data(name='dset', value=[1,2,3], is_cached=False, 
      cache_if_not_exists=True)
    
    self.assertListEqual(gp.get_data(key='dset'), [1,2,3])
    
  def test_todict(self):
    gp = self.ensure()
    # make sure can be turned to dictionary
    gp.to_dict()
  
class TestKeyframes(TestCase):
  def test_keyframe(self):
    kf = c.KeyFrame(name='testkf', value=1, time = 0)
    self.assertListEqual(kf._time, [0])
    self.assertListEqual(kf._values, [1])
    
    tf = pu.tempfile()
    self.assertFalse(kf.cached)
    kf.use_cache(path = tf, name='testcachekf')
    self.assertTrue(kf.cached)
    
    # no error should occur
    pu.from_json(from_file=tf)
    
    try:
      kf = c.KeyFrame(name='testkf', value=[0,1], time = 0)
      self.assertFalse(True, msg='Keyframe expect failure')
    except Exception as e:
      pass
  
  def test_kfprop_cont(self):
    # continuous case
    time = [x for x in range(10)]
    value = [x-5 for x in range(10)]
    kf = c.KeyFrame(name='testkf', value=value, time = time)
    
    self.assertTrue(kf.value_names is None)
    self.assertTrue(kf.is_continuous)
    self.assertListEqual(kf.value_range, [-5,4])
    
    tf = pu.tempfile()
    kf.use_cache(path = tf, name='testcachekf')
    self.assertTrue(kf.value_names is None)
    self.assertTrue(kf.is_continuous)
    self.assertListEqual(kf.value_range, [-5,4])
    
  def test_kfprop_disc(self):
    # discrete case
    time = [x for x in range(5)]
    value = ['a', 'B', 'c', 'a', 'c']
    kf = c.KeyFrame(name='testkf', value=value, time = time, 
      dtype='discrete')
    
    self.assertTrue(len(kf.value_names) == 3)
    self.assertFalse(kf.is_continuous)
    self.assertTrue(kf.value_range is None)
    
    tf = pu.tempfile()
    kf.use_cache(path = tf, name='testcachekf')
    self.assertTrue(len(kf.value_names) == 3)
    self.assertFalse(kf.is_continuous)
    self.assertTrue(kf.value_range is None)

class TestColorMaps(TestCase):
  def test_initcmap(self):
    s = c.SphereGeom(name='s1', position=[1,2,3], radius=3)
    s.set_value(name='v1', value=[1,2,3], time_stamp=[0,-1,2])
    cmap = c.ColorMap('v1', geoms = [s], symmetric = 0, alias = None)
    cdict = cmap.to_dict()
    self.assertListEqual(cmap.time_range, [-1,2])
    self.assertListEqual(cmap.value_range, [1,3])
    self.assertTrue(len(cdict['color_keys']) == 64)
    self.assertTrue(len(cdict['color_vals']) == 64)
    
  def test_cmap_continuous(self):
    geoms = []
    for i in range(3):
      s = c.SphereGeom(name='s%d' %i)
      s.set_value(name='v1', value=[1,2,3 + i], time_stamp=[0,-1-i,2])
      geoms.append(s)
    cmap = c.ColorMap('v1', geoms = geoms, symmetric = 0, alias = 'lol')
    cmap.hard_range = [-1,1]
    cdict = cmap.to_dict()
    self.assertListEqual(cmap.time_range, [-3,2])
    self.assertListEqual(cmap.value_range, [1,5])
    self.assertTrue(len(cdict['color_keys']) == 64)
    self.assertTrue(len(cdict['color_vals']) == 64)
    self.assertEqual(cdict['alias'], 'lol')
    self.assertListEqual(cdict['hard_range'], [-1,1])
  
  def test_cmap_discrete(self):
    geoms = []
    for i in [0,1,2,3]:
      s = c.SphereGeom(name='s%d' % i)
      s.set_value(name='v1', value=[string.ascii_letters[i]])
      geoms.append(s)
    cmap = c.ColorMap('v1', geoms = geoms, symmetric = 0, alias = 'lol')
    self.assertEqual(cmap.value_type, 'discrete')
    
    self.assertListEqual( cmap.value_names, 
      [s.animation_value_names('v1')[0] for s in geoms])
    
    cmap.to_dict()

class TestGeoms(TestCase):
  
  def test_abstract_geom(self):
    gp = c.GeomGroup(name='test*group', layer=[0,1])
    geom = c.AbstractGeom(name='absgeom', position = [0,0,2], 
                group = gp, layer = [0,3] )
    
    geom.to_dict()
    
    geom.custom_info = 'lol'
    
    geom.set_position(1,2,3)
    self.assertListEqual(geom.position, [1,2,3])
    
    gp.set_group_data(name='dset1', value=[1,2,3,4], is_cached=False, 
      cache_if_not_exists=True)
    self.assertListEqual(geom.get_data('dset1'), [1,2,3,4])
    
    geom.set_value('dset1', value = [1,2, math.nan], time_stamp=[0,1,2])
    self.assertTrue('dset1' in geom.keyframes)
    kf = geom.keyframes['dset1']
    self.assertListEqual(geom.get_data('dset1'), [1,2])
    
  def test_blank_geom(self):
    gp = c.GeomGroup(name='test*group', layer=[0,1])
    geom = c.BlankGeom(gp)
    geom = c.BlankGeom(gp, name = '213')
    geom.to_dict()
    pass
  
  def test_sphere_geom(self):
    s = c.SphereGeom(name='s1', position=[1,2,3], radius=3)
    s.to_dict()
    pass
