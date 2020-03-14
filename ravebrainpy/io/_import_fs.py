#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import numpy as np
from .. import IDENTITY4X4, SURFACE_TYPES
from ..utils import read_from_file, stopifnot, digest_file, file_exists
from ..utils import as_dict, unlink, from_json, to_json, make_dirs
from ..utils import json_cache, check_digestfile, normalize_path
from ..core import GeomGroup, FreeGeom, DataCubeGeom
# from ravebrainpy.utils import *
# from ravebrainpy.core import *
ravebrainpy_data_ver = 1

# fspath = '/Users/beauchamplab/rave_data/others/three_brain/YCQ/'
# subject_code = 'YCQ'
# surf_type = 'pial'
# hemisphere='l'

if False:
  from ravebrainpy.core.import_fs import import_freesurfer
  fspath = '/Users/beauchamplab/rave_data/data_dir/demo/YAB/fs/'
  import_freesurfer('YAB', fspath)

def reorient_volume( volume, Norig ):
  order_index = np.matmul(
    np.array(Norig),
    np.array([[1],[2],[3],[0]]))
  order_index = order_index.flatten()[:3].astype(int)
  # reorder
  volume = volume.transpose(np.abs(order_index) - 1)
  # flip
  flip_idx = np.argwhere(order_index < 0).flatten().tolist()
  if len(flip_idx) > 0:
    flip_idx = tuple(flip_idx)
    volume = np.flip(volume, flip_idx)
  return volume

def _import_fs_T1(subject_code, fspath):
  mri_path = os.path.join(fspath, 'mri')
  rave_path = os.path.join(fspath, 'RAVEpy')
  make_dirs(rave_path)
  
  # Step 1: Find t1 volume data
  t1_image = [
    "brain.finalsurfs.mgz", "brainmask.mgz", 
    "brainmask.auto.mgz", "T1.mgz"
  ]
  
  t1_paths = [os.path.join(mri_path, x) for x in t1_image]
  fe = [os.path.exists(x) for x in t1_paths]
  
  stopifnot(any(fe), msg='''
  Cannot find T1 images. None of the following files exist:
    mri/%s
  ''' % '\n    mri/'.join(t1_image))

  # Step 2: Check T1 with existing signature
  t1_name = [x for x,y in zip(t1_image, fe) if y][0]
  t1_path = [x for x,y in zip(t1_paths, fe) if y][0]
  cache_name = '%s_t1.json' % subject_code
  cache_volume = os.path.join(rave_path, cache_name)
  cache_digest = cache_volume + '.pydigest'

  # Check if cache_volume exists
  has_cache = False
  file_digest = digest_file(t1_path, length=20, mode='rb')
  
  # 1. check original file vs digest
  if file_exists(cache_volume) and file_exists(cache_digest):
    # Check digest
    json_digest = digest_file(cache_volume, length=20)
    tmp = from_json(from_file=cache_digest)
    if tmp.get('digest_origin', '') == file_digest and \
      tmp.get('digest', '') == json_digest and \
      tmp.get('ravebrainpy_data_ver', 0) >= ravebrainpy_data_ver:
      has_cache = True
  
  if has_cache:
    return False

  # Step 3: read-in file, create cache
  import nibabel
  brain_t1 = nibabel.load(t1_path)
  Norig = brain_t1.header.get_vox2ras()
  Torig = brain_t1.header.get_vox2ras_tkr()
  
  group_volume = GeomGroup(name='Volume - T1 (%s)' % subject_code)
  group_volume.subject_code = subject_code
  
  
  volume = brain_t1.get_fdata().astype(np.uint8)
  volume = reorient_volume( volume, Norig )
  volume_shape = list(volume.shape)
  volume = volume.flatten('F').tolist()
  
  # recache
  unlink(cache_volume)
  unlink(cache_digest)
  
  DataCubeGeom(
    name = 'T1 (%s)' % subject_code,
    value = volume,
    dim = volume_shape,
    half_size = [x/2.0 for x in volume_shape],
    group = group_volume,
    position = [0,0,0],
    cache_file = cache_volume
  )
  
  # generate file_digest
  json_digest = digest_file(file=cache_volume, length=20)
  
  # add additional information to cache_digest
  dinfo = from_json(from_file=cache_digest)
  dinfo['digest'] = json_digest
  dinfo['digest_origin'] = file_digest
  dinfo['Norig'] = Norig.tolist()
  dinfo['Torig'] = Torig.tolist()
  dinfo['source_name'] = t1_name
  dinfo['shape'] = volume_shape
  dinfo['ravebrainpy_data_ver'] = ravebrainpy_data_ver
  
  to_json(dinfo, to_file=cache_digest)
  
  # Add to common.digest
  common_file = os.path.join(rave_path, 'common.pydigest')
  if file_exists(common_file):
    dinfo = from_json(from_file=common_file)
  else:
    dinfo = {}
  
  fv = dinfo.get('fs_volume_files', [])
  if not cache_name in fv:
    fv.append(cache_name)
  dinfo['Norig'] = Norig.tolist()
  dinfo['Torig'] = Torig.tolist()
  dinfo['fs_volume_files'] = fv
  to_json(dinfo, to_file=common_file)
  return True

def _import_fs_surf(subject_code, fspath, surf_type, hemisphere):
  surf_path = os.path.join(fspath, 'surf')
  rave_path = os.path.join(fspath, 'RAVEpy')
  make_dirs(rave_path)
  
  # Step 1: Find surface data (reuse code so variable name mismatches)
  t1_image = ["%sh.%s", "%sh.%s.asc"]
  t1_image = [x % (hemisphere, surf_type) for x in t1_image]
  
  t1_paths = [os.path.join(surf_path, x) for x in t1_image]
  fe = [os.path.exists(x) for x in t1_paths]
  
  stopifnot(any(fe), msg='''
  Cannot find FreeSurfer Surface files. None of the file exists:
    surf/%s
  ''' % '\n    surf/'.join(t1_image))

  # Step 2: Check T1 with existing signature
  surf_fname = [x for x,y in zip(t1_image, fe) if y][0]
  surf_path = [x for x,y in zip(t1_paths, fe) if y][0]
  
  cache_name = '%s_fs_%sh_%s.json' % (
    subject_code, hemisphere, surf_type
  )
  cache_surf = os.path.join(rave_path, cache_name)
  cache_digest = cache_surf + '.pydigest'

  # Check if cache_surf exists
  has_cache = False
  file_digest = digest_file(surf_path, mode='rb')

  # 1. check original file vs digest
  if file_exists(cache_surf) and file_exists(cache_digest):
    # Check digest
    json_digest = digest_file(cache_surf, length=20)
    tmp = from_json(from_file=cache_digest)
    if tmp.get('digest_origin', '') == file_digest and \
      tmp.get('digest', '') == json_digest and \
      tmp.get('ravebrainpy_data_ver', 0) >= ravebrainpy_data_ver:
      has_cache = True

  if has_cache:
    return False
  
  # Step 3: Create cache
  surf_group = GeomGroup(
    name = 'Surface - %s (%s)' % (surf_type, subject_code),
    position = [0,0,0])
  
  full_hemisphere = 'Left' if hemisphere == 'l' else 'Right'
  
  # if surf_path ends with asc
  if surf_path.endswith('asc'):
    with open(surf_path, 'r') as f:
      s = f.readline()
      while s.startswith('#'):
        s = f.readline()
      # header
      tmp = re.split(r'[^0-9]+', s)
      nvert = int(tmp[0])
      nface = int(tmp[1])
      vertex = [f.readline() for x in range(nvert)]
      face = [f.readline() for x in range(nface)]
    # extract vertex and face
    
    vertex = [[float(v) for v in re.split(r'[ ]+', x)[:3]] for x in vertex]
    face = [[int(v) for v in re.split(r'[ ]+', x)[:3]] for x in face]
  else:
    import nibabel
    tmp = nibabel.freesurfer.io.read_geometry(
      surf_path,read_metadata=False)
    vertex = tmp[0][:,:3].tolist()
    face = tmp[1][:,:3].tolist()
  
  unlink(cache_surf)
  
  FreeGeom(
    name = 'FreeSurfer %s Hemisphere - %s (%s)' % (
      full_hemisphere, surf_type, subject_code,
    ), position = [0,0,0], cache_file = cache_surf, 
    group = surf_group, layer = [8], vertex = vertex, face = face)
  
  # Add file_digest, Norig, Torig to cache_digest
  dinfo = from_json(from_file=cache_digest)
  dinfo['digest'] = digest_file(cache_surf)
  dinfo['digest_origin'] = file_digest
  dinfo['surface_format'] = 'fs'
  dinfo['hemisphere'] = hemisphere
  dinfo['ravebrainpy_data_ver'] = ravebrainpy_data_ver
  dinfo['n_vertices'] = len(vertex)
  dinfo['n_faces'] = len(face)
  dinfo['is_surface'] = True
  dinfo['is_fs_surface'] = True
  
  to_json(dinfo, to_file=cache_digest)
  return True

def _import_fs_curv(subject_code, fspath, curv_name, hemisphere):
  surf_path = os.path.join(fspath, 'surf')
  rave_path = os.path.join(fspath, 'RAVEpy')
  make_dirs(rave_path)
  
  # Step 1: Find surface data (reuse code so variable name mismatches)
  t1_image = ["%sh.%s", "%sh.%s.asc"]
  t1_image = [x % (hemisphere, curv_name) for x in t1_image]
  
  t1_paths = [os.path.join(surf_path, x) for x in t1_image]
  fe = [os.path.exists(x) for x in t1_paths]
  
  stopifnot(any(fe), msg='''
  Cannot find FreeSurfer curv/sulc files. None of the file exists:
    surf/%s
  ''' % '\n    surf/'.join(t1_image))

  # Step 2: Check T1 with existing signature
  surf_fname = [x for x,y in zip(t1_image, fe) if y][0]
  surf_path = [x for x,y in zip(t1_paths, fe) if y][0]
  
  cache_name = '%s_fs_%sh_%s.json' % (
    subject_code, hemisphere, curv_name
  )
  cache_surf = os.path.join(rave_path, cache_name)
  cache_digest = cache_surf + '.pydigest'

  # Check if cache_surf exists
  has_cache = False
  file_digest = digest_file(surf_path, mode='rb')

  # 1. check original file vs digest
  if file_exists(cache_surf) and file_exists(cache_digest):
    # Check digest
    json_digest = digest_file(cache_surf, length=20)
    tmp = from_json(from_file=cache_digest)
    if tmp.get('digest_origin', '') == file_digest and \
      tmp.get('digest', '') == json_digest and \
      tmp.get('ravebrainpy_data_ver', 0) >= ravebrainpy_data_ver:
      has_cache = True

  if has_cache:
    return False
  
  # Step 3: Create cache
  full_hemisphere = 'Left' if hemisphere == 'l' else 'Right'
  
  # if surf_path ends with asc
  if surf_path.endswith('asc'):
    with open(surf_path, 'r') as f:
      curv = [s.strip().split(' ').pop() for s in f]
      curv = [float(x) for x in curv]
  else:
    import nibabel
    # nibabel.freesurfer.io.read_morph_data('/Users/beauchamplab/rave_data/others/three_brain/YCQ/surf/lh.sulc')
    tmp = nibabel.freesurfer.io.read_morph_data(surf_path)
    curv = tmp.tolist()
  
  unlink(cache_surf)
  
  # Check with fs vertex_count
  pial_info = from_json(from_file=os.path.join(
    rave_path, '%s_fs_%sh_pial.json.pydigest' % (
    subject_code, hemisphere)))
  
  n_vertices = pial_info.get('n_vertices', None)
  if n_vertices is not None and n_vertices != len(curv):
    print("WARNING: '%s' does not agree with pial surface on vertex count" % surf_fname)

  # save to cache
  dset_name = 'Curvature - %sh.%s (%s)' % (hemisphere, curv_name, subject_code)
  
  json_cache(cache_surf, { dset_name : {
    'name' : curv_name,
    'full_name' : dset_name,
    'cached' : True,
    'hemisphere' : hemisphere,
    'n_points' : len(curv),
    'range' : [min(curv), max(curv)],
    'value' : curv
  }})
  
  # Add file_digest, Norig, Torig to cache_digest
  dinfo = from_json(from_file=cache_digest)
  dinfo['digest'] = digest_file(cache_surf)
  dinfo['digest_origin'] = file_digest
  dinfo['curve_format'] = 'fs'
  dinfo['curve_name'] = curv_name
  dinfo['hemisphere'] = hemisphere
  dinfo['ravebrainpy_data_ver'] = ravebrainpy_data_ver
  dinfo['n_points'] = len(curv)
  dinfo['is_sulc'] = True
  dinfo['is_fs_sulc'] = True
  
  to_json(dinfo, to_file=cache_digest)
  return True


def import_freesurfer(subject_code, fspath, force=False):
  
  fspath = normalize_path(fspath)
  
  curvatures = ['sulc']
  
  if force:
    rave_path = os.path.join(fspath, 'RAVEpy')
    if file_exists(rave_path):
      print('Clean previous files')
      cached_files = os.listdir(rave_path)
      sel=[len(re.findall(r'pydigest$', x)) > 0 for x in cached_files]
      cached_files = [x for x,y in zip(cached_files, sel) if y]
      for f in cached_files:
        unlink(os.path.join(rave_path, f))
  
  print('-------------------- Load T1 volume --------------------')
  try:
    cached = _import_fs_T1(subject_code, fspath)
    if not cached:
      print('No need to update')
  except Exception as e:
    print('Missing file or import error')
    print(e)
  
  
  print('--------------- Load FreeSurfer Surfaces ---------------')
  for surf_type in SURFACE_TYPES:
    print('### ' + surf_type)
    try:
      cached1 = _import_fs_surf(subject_code, fspath, surf_type, 'l')
      cached2 = _import_fs_surf(subject_code, fspath, surf_type, 'r')
      if not cached1 and not cached2:
        print('No need to update')
    except Exception as e:
      print('Missing file or import error')
  
  print('------------------ Load curvature data -----------------')
  for curv in curvatures:
    print('### ' + curv)
    try:
      cached1 = _import_fs_curv(subject_code, fspath, curv, 'l')
      cached2 = _import_fs_curv(subject_code, fspath, curv, 'r')
      if not cached1 and not cached2:
        print('No need to update')
    except Exception as e:
      print('Missing file or import error')
  
  # Load xfm
  path_xform = normalize_path(os.path.join(
    fspath, 'mri', 'transforms', 'talairach.xfm'
  ))
  
  xfm = read_from_file( path_xform )
  pattern = '([-]{0,1}[0-9.]+)'
  pattern = r'^%s[ ]+%s[ ]+%s[ ]+%s[;]{0,1}$' % (
    pattern,pattern,pattern,pattern)
  xfm = [[float(v) for v in m.groups()] for m in (
    re.match(pattern, x) for x in xfm
  ) if m is not None]
  # flatten
  xfm = [item for items in xfm for item in items]
  
  if len(xfm) < 12:
    print('Cannot parse "mri/transforms/talairach.xfm" to get xform')
    xfm = IDENTITY4X4
  else:
    xfm = xfm[:12]
    xfm.extend([0,0,0,1])
  # Save to common.pydigest
  common_file = os.path.join(fspath, 'RAVEpy', 'common.pydigest')
  if file_exists(common_file):
    dinfo = from_json(from_file=common_file)
  else:
    dinfo = {}
  
  dinfo['xfm'] = xfm
  to_json(dinfo, to_file=common_file)


