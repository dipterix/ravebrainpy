#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import string 
import random
import numpy as np
import pandas as pd

def stopifnot(*args, **kargs):
  msg = kargs.pop('msg', '(Error message not provided)')
  for v in args:
    if not v:
      raise Exception(msg)
  for k in kargs:
    if not kargs[k]:
      raise Exception(msg)
  return True
  

def rand_string(length = 10):
  ltr = string.ascii_letters + string.digits
  return ''.join([random.sample(ltr, 1)[0] for x in range(length)])

def as_dict( x, dataframe = 'row', matrix = 'rowmajor' ):
  if isinstance(x, (list, tuple,)):
    return [as_dict(item) for item in x]
  
  if isinstance(x, dict):
    return dict([(key, as_dict(item)) for key, item in x.items()])
  
  if isinstance(x, set):
    return list(x)
  
  if isinstance(x, (np.ndarray, np.matrix, )):
    if matrix != 'rowmajor':
      x = x.T
    return x.tolist()
  
  if isinstance(x, pd.DataFrame):
    if dataframe != 'row':
      return x.to_dict(orient='list')
    return x.to_dict(orient='records')
  
  return x

def spread_list(x, expected_length=[]):
  l = as_dict(x)
  x = []
  for v in l:
    if isinstance(v, (list, tuple, )):
      x.extend(list(v))
    else:
      x.append(v)
  if len(expected_length):
    stopifnot(len(x) in expected_length,
      msg='''
      x does not match required length:
        Asking for one of the following lengths [%s]
        Provided length %d
      ''' % (
        ','.join([str(i) for i in expected_length]),
        len(x)
      ))
  return x


def matmult4x4(m1, m2):
  m1 = spread_list(m1, [16])
  m2 = spread_list(m2, [16])
  a11,a12,a13,a14,a21,a22,a23,a24,a31,a32,a33,a34,a41,a42,a43,a44=tuple(m1)
  b11,b12,b13,b14,b21,b22,b23,b24,b31,b32,b33,b34,b41,b42,b43,b44=tuple(m2)
  return (
    a11*b11+a12*b21+a13*b31+a14*b41,
    a11*b12+a12*b22+a13*b32+a14*b42,
    a11*b13+a12*b23+a13*b33+a14*b43,
    a11*b14+a12*b24+a13*b34+a14*b44,
    
    a21*b11+a22*b21+a23*b31+a24*b41,
    a21*b12+a22*b22+a23*b32+a24*b42,
    a21*b13+a22*b23+a23*b33+a24*b43,
    a21*b14+a22*b24+a23*b34+a24*b44,
    
    a31*b11+a32*b21+a33*b31+a34*b41,
    a31*b12+a32*b22+a33*b32+a34*b42,
    a31*b13+a32*b23+a33*b33+a34*b43,
    a31*b14+a32*b24+a33*b34+a34*b44,
    
    a41*b11+a42*b21+a43*b31+a44*b41,
    a41*b12+a42*b22+a43*b32+a44*b42,
    a41*b13+a42*b23+a43*b33+a44*b43,
    a41*b14+a42*b24+a43*b34+a44*b44,
  )


def inv4x4(m):
  m = spread_list(m, [16])
  n11,n12,n13,n14,n21,n22,n23,n24,n31,n32,n33,n34,n41,n42,n43,n44=tuple(m)
  t11=n23*n34*n42-n24*n33*n42+n24*n32*n43-n22*n34*n43-n23*n32*n44+n22*n33*n44
  t12=n14*n33*n42-n13*n34*n42-n14*n32*n43+n12*n34*n43+n13*n32*n44-n12*n33*n44
  t13=n13*n24*n42-n14*n23*n42+n14*n22*n43-n12*n24*n43-n13*n22*n44+n12*n23*n44
  t14=n14*n23*n32-n13*n24*n32-n14*n22*n33+n12*n24*n33+n13*n22*n34-n12*n23*n34
  det=n11*t11+n21*t12+n31*t13+n41*t14
  stopifnot(det != 0, msg='Cannot inverse matrix as determinant is 0')
  detInv = 1.0 / det;
  te = [x for x in m]

  te[0] = t11 * detInv
  te[4]=(n24*n33*n41-n23*n34*n41-n24*n31*n43+n21*n34*n43+n23*n31*n44-n21*n33*n44)*detInv
  te[8]=(n22*n34*n41-n24*n32*n41+n24*n31*n42-n21*n34*n42-n22*n31*n44+n21*n32*n44)*detInv
  te[12]=(n23*n32*n41-n22*n33*n41-n23*n31*n42+n21*n33*n42+n22*n31*n43-n21*n32*n43)*detInv

  te[1]=t12*detInv
  te[5]=(n13*n34*n41-n14*n33*n41+n14*n31*n43-n11*n34*n43-n13*n31*n44+n11*n33*n44)*detInv
  te[9]=(n14*n32*n41-n12*n34*n41-n14*n31*n42+n11*n34*n42+n12*n31*n44-n11*n32*n44)*detInv
  te[13]=(n12*n33*n41-n13*n32*n41+n13*n31*n42-n11*n33*n42-n12*n31*n43+n11*n32*n43)*detInv

  te[2]=t13*detInv
  te[6]=(n14*n23*n41-n13*n24*n41-n14*n21*n43+n11*n24*n43+n13*n21*n44-n11*n23*n44)*detInv
  te[10]=(n12*n24*n41-n14*n22*n41+n14*n21*n42-n11*n24*n42-n12*n21*n44+n11*n22*n44)*detInv
  te[14]=(n13*n22*n41-n12*n23*n41-n13*n21*n42+n11*n23*n42+n12*n21*n43-n11*n22*n43)*detInv

  te[3]=t14*detInv
  te[7]=(n13*n24*n31-n14*n23*n31+n14*n21*n33-n11*n24*n33-n13*n21*n34+n11*n23*n34)*detInv
  te[11]=(n14*n22*n31-n12*n24*n31-n14*n21*n32+n11*n24*n32+n12*n21*n34-n11*n22*n34)*detInv
  te[15]=(n12*n23*n31-n13*n22*n31+n13*n21*n32-n11*n23*n32-n12*n21*n33+n11*n22*n33)*detInv
  
  return te
