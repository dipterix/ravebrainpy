#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import TestCase
import tempfile
import os
import ravebrainpy
import ravebrainpy.utils as pyutils
import numpy as np
import pandas as pd
import json

class TestUtils(TestCase):
  
  _d = {
    'a' : [None],
    'b' : np.array([[1,2,3], [1.2,2.3,3.4]]),
    'c' : pd.DataFrame([[1,2,3], [1.2,2.3,3.4]], index=['a', 'b'],
          columns=['A','B','C'])
  }
  _r = None
  
  def todict(self):
    if self._r is None:
      self._r = pyutils.as_dict(self._d)
    return self._r
  
  def test_hello(self):
    s = ravebrainpy.hello()
    self.assertTrue(s)
    
  def test_dict2json(self):
    self.todict()
    self.assertDictEqual(
      self._r,
      {'a': [None], 'b': [[1.0, 2.0, 3.0], [1.2, 2.3, 3.4]], 
      'c': [{'A': 1.0, 'B': 2.0, 'C': 3.0}, 
            {'A': 1.2, 'B': 2.3, 'C': 3.4}]}
    )
  
  def test_tojson(self):
    with tempfile.TemporaryDirectory('ravebrainpytest') as tmpdir:
      # tmpdir = tempfile.TemporaryDirectory('ravebrainpytest')
      test_file = os.path.join(tmpdir, 'yoyo/test.json/')
      test_file = pyutils.normalize_path( test_file )
      if os.path.exists( test_file ):
        os.remove( test_file )
      self.assertFalse( os.path.exists( test_file ) )
      
      # dict to json save file
      pyutils.to_json(self._d, to_file=test_file)
      self.assertTrue( os.path.exists( test_file ) )
      
      self.assertDictEqual(
        pyutils.from_json( from_file = test_file ),
        self.todict()
      )
      pass
    
  def test_digest(self):
    s = pyutils.digest(123, length=10)
    self.assertTrue(isinstance(s, str))
    self.assertTrue(len(s) == 10)
  

# class TestRenderer(TestCase):
#   def test_path(self):
#     s = ravebrainpy.core.render_threejsbrain()
#     self.assertTrue(isinstance(s, str))
