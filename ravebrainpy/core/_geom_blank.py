#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ..utils import rand_string
from ._geom_abs import AbstractGeom
class BlankGeom(AbstractGeom):
  
  def set_value(self, *args, **kwargs):
    pass
  
  def __init__(self, group, name=rand_string(20), **kwargs):
    super().__init__(name = name, **kwargs)
    self.geom_type = 'blank'
    self.value = None
    self.clickable = False
    self.layer = set([31])
    self.clickable = False
    self.group = group

