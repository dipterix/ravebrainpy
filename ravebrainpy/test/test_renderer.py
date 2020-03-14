#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import TestCase
import ravebrainpy.core as c
import ravebrainpy.utils as pu

if False:
  self = TestCase()

class TestRenderer(TestCase):
  def test_sphere(self):
    geoms = []
    gp = c.GeomGroup(name='test*group', layer=[0,1], position=[0,10,0])
    for i in range(3):
      s = c.SphereGeom(name='s%d' %i, position=[i*10, 0, 0], group = gp)
      s.set_value(name='v1', value=[1,2,3 + i], time_stamp=[0,-1-i,2])
      geoms.append(s)
    
    s = c.render_threejsbrain(geoms=geoms, debug=True)
    self.assertTrue(isinstance(s, str))
    if False:
      c.start_viewer(s)
