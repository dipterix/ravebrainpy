#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import numpy as np
from .. import SURFACE_TYPES, IDENTITY4X4
from ..utils import stopifnot, as_dict, normalize_path, file_exists
from ..utils import from_json, spread_list, matmult4x4, inv4x4
from ..utils import normalize_path
from . import GeomGroup, FreeGeom, DataCubeGeom, BlankGeom
from . import render_threejsbrain

OFFSETS = {
  'inflated' : 50,
  'sphere' : 128
}


def _spread_4x4(x):
  x = spread_list(x, expected_length=[12,16])
  if len(x) == 12:
    x.extend([0,0,0,1])
  return x

class Brain:
  
  @property
  def xfm(self):
    x = self._xfm
    return [[x[i+j] for j in range(4)] for i in [0,4,8,12]]
  
  @xfm.setter
  def xfm(self, x):
    self._xfm = _spread_4x4(x)
  
  @property
  def Norig(self):
    x = self._Norig
    return [[x[i+j] for j in range(4)] for i in [0,4,8,12]]
  
  @Norig.setter
  def Norig(self, x):
    self._Norig = _spread_4x4(x)
  
  @property
  def Torig(self):
    x = self._Torig
    return [[x[i+j] for j in range(4)] for i in [0,4,8,12]]
  
  @Torig.setter
  def Torig(self, x):
    self._Torig = _spread_4x4(x)
  
  def _import_from_fspath(self, path):
    stopifnot(path is not None and file_exists(path),
      msg="Must specify a valid subject's FreeSurfer path")
    stopifnot(file_exists(os.path.join(path, 'RAVEpy')),
      msg="Please use 'import_freesurfer' to import FreeSurfer files")
    
    path = normalize_path(path)
    _p = self._paths
    _p['root'] = path
    _p['ravepy_path'] = os.path.join(path, 'RAVEpy')
    _p['digest'] = os.path.join( _p['ravepy_path'], 'common.pydigest' )
    # 1. read common.pydigest
    info = from_json(from_file=_p['digest'])
    if 'xfm' in info:
      self.xfm = info['xfm']
    if 'Norig' in info:
      self.Norig = info['Norig']
    if 'Torig' in info:
      self.Torig = info['Torig']
    
    # load volumes
    self._load_volume('T1')
  
  def _load_surface(self, surface_type):
    stopifnot(surface_type in SURFACE_TYPES,
      msg = 'surface type must be one of the followings:\n\t%s' % (
        ', '.join(SURFACE_TYPES)
      ))
    rave_path = self._paths['ravepy_path']
    subject_code = self.subject_code
    gp = GeomGroup(name='Surface - %s (%s)' % (
      surface_type, subject_code))
    cache_file=os.path.join(rave_path, '%s_fs_lh_%s.json' % (subject_code, surface_type))
    lvert_name = 'FreeSurfer Left Hemisphere - %s (%s)' % (surface_type, subject_code)
    gleft = FreeGeom(lvert_name,cache_file=cache_file, group=gp)
    
    cache_file=os.path.join(rave_path, '%s_fs_rh_%s.json' % (subject_code, surface_type))
    rvert_name = 'FreeSurfer Right Hemisphere - %s (%s)' % (surface_type, subject_code)
    gright = FreeGeom(rvert_name, cache_file=cache_file,group=gp)
    surface = BrainSurface(
      subject_code=subject_code, surface_type=surface_type,
      mesh_type='fs', left_hemisphere=gleft, right_hemisphere=gright)
    self.add_surface(surface=surface)
    return surface
  
  def _load_volume(self, volume_type = 'T1'):
    rave_path = self._paths['ravepy_path']
    if volume_type == 'T1':
      gp_vol = GeomGroup(name='Volume - T1 (%s)' % self.subject_code)
      cache_path = os.path.join(rave_path, '%s_t1.json' % self.subject_code)
      cube = DataCubeGeom(
        name='T1 (%s)' % self.subject_code, 
        group=gp_vol, cache_file=cache_path)
      volume = BrainVolume(
        subject_code=self.subject_code, volume_type='T1', volume=cube)
      self.add_volume(volume=volume)
    return volume
  
  def _load_surface_color(self, surface_type, vertex_color):
    rave_path = self._paths['ravepy_path']
    subject_code = self.subject_code
    
    lvert_name = 'Curvature - lh.%s (%s)' % (vertex_color, subject_code)
    rvert_name = 'Curvature - rh.%s (%s)' % (vertex_color, subject_code)
    
    surf = self.surfaces.get(surface_type, None)
    if surf is not None:
      surf.group.set_group_data(name='curvature', value=vertex_color)
      surf.group.set_group_data('default_vertex_lh_%s' % surface_type, lvert_name)
      surf.group.set_group_data('default_vertex_rh_%s' % surface_type, rvert_name)
    
    curv_lh = os.path.join(
      rave_path, 
      '%s_fs_lh_%s.json' % (subject_code, vertex_color))
    
    
    self.add_vertex_color(name = lvert_name, path = curv_lh)
    
    curv_rh = os.path.join(
      rave_path, 
      '%s_fs_rh_%s.json' % (subject_code, vertex_color))
    
    self.add_vertex_color(name = rvert_name, path = curv_rh)
  
  def __init__(self, subject_code, path=None, **kwargs):
    self._subject_code = subject_code
    self._xfm = IDENTITY4X4
    self._Norig = IDENTITY4X4
    self._Torig = IDENTITY4X4
    self.meta = {}
    self.surfaces = {}
    self.volumes = {}
    self.misc = BlankGeom(
      group = GeomGroup('_internal_group_data_%s' % subject_code),
      name = '_misc_%s' % subject_code
    )
    self._paths = {}
    # TODO
    self.electrodes = {}
    self.xfm = kwargs.get('xfm', IDENTITY4X4)
    self.Norig = kwargs.get('Norig', IDENTITY4X4)
    self.Torig = kwargs.get('Torig', IDENTITY4X4)
    
    if path is not None and file_exists(path):
      self._import_from_fspath(path)
      surfaces=kwargs.get('surfaces', ['pial'])
      surface_color = kwargs.get('surface_colors', 'sulc')
      
      for surf_type in surfaces:
        try:
          self._load_surface(surf_type)
          self._load_surface_color(surf_type, surface_color)
        except Exception as e:
          print('Failed to load surface type %s. Reasons:' % surf_type)
          print(e)
    pass
  
  def add_surface(self, surface):
    stopifnot(isinstance(surface, BrainSurface),
      msg = 'surface must be BrainSurface instance')
    stopifnot(surface.has_hemispheres, msg="surface missing mesh?")
    
    if surface.mesh_type == 'std.141':
      surface.set_group_position( self.scanner_center )
      # inflated and sphere have offsets
      offset_x = OFFSETS.get(surface.surface_type, 0)
      surface.left_hemisphere.position = [-offset_x, 0, 0]
      surface.right_hemisphere.position = [offset_x, 0, 0]
    elif surface.mesh_type == 'fs':
      surface.set_group_position( 0, 0, 0 )
      surface.left_hemisphere.position = [0, 0, 0]
      surface.right_hemisphere.position = [0, 0, 0]
    
    surface.set_subject_code( self.subject_code )
    self.surfaces[ surface.surface_type ] = surface
    pass
  
  def remove_surface(self, surface_types = []):
    for s in surface_types:
      yield self.surfaces.pop(s, None)
  
  def add_volume(self, volume):
    stopifnot( isinstance(volume, BrainVolume),
      msg='volume must be a BrainVolume instance')
    stopifnot( volume.has_volume,
      msg='volume missing data')
    
    volume.set_subject_code( self.subject_code )
    self.volumes[ volume.volume_type ] = volume
  
  def remove_volume(self, volume_types=[]):
    for s in volume_types:
      yield self.volumes.pop( s, None )
  
  def add_vertex_color(self, name, path, lazy=True):
    path = normalize_path(path)
    self.misc.group.set_group_data(
      name = name,
      value = {
        'path' : path,
        'absolute_path' : path,
        'file_name' : os.path.basename(path),
        'is_new_cache' : False,
        'is_cache' : True,
        'lazy' : lazy
      },
      is_cached = True
    )
  
  def set_electrodes(self, electrodes):
    # TODO
    pass
  
  def set_electrode_values(self, table_or_path):
    #TODO
    pass
  def calculate_template_coordinates(save_to = 'auto'):
    #TODO
    pass
  def get_geometries(self, volumes=True,surfaces=True,electrodes=True):
    geoms = [self.misc]
    
    # get volumes
    if volumes == True:
      volumes = self.volume_types
    elif volumes == False:
      volumes = []
    for v in volumes:
      item = self.volumes.get( v, None )
      if item is not None and isinstance(item, BrainVolume):
        geoms.append( item._object )
    
    # get surfaces
    if surfaces == True:
      surfaces = self.surface_types
    if surfaces == False:
      surfaces = []
    for s in surfaces:
      item = self.surfaces.get( s, None )
      if item is not None and isinstance(item, BrainSurface):
        geoms.append( item.left_hemisphere )
        geoms.append( item.right_hemisphere )
    
    if electrodes == True:
      # TODO
      pass
    
    return geoms
  
  def render(self, 
    volumes = True, surfaces = True, start_zoom = 1, font_scale = 1,
    background = '#FFFFFF', side_canvas = True, side_width = 150, 
    side_shift = [0,0], side_display = True, control_panel = True, 
    control_display = True, default_colormap = None,
    palettes = {}, control_presets = [], coords=None,
    value_alias = {},
    value_ranges = {}, controllers = {}, start_server = True,
    **kwargs):
    
    # collect volume information
    geoms = self.get_geometries( 
      volumes = volumes, surfaces = surfaces, electrodes = True )

    global_data = self.global_data
    
    presets = [
      'subject2', 'surface_type2', 'hemisphere_material',
      'map_template', 'electrodes'
    ]
    for p in control_presets:
      if not p in presets:
        presets.append( p )
    for p in ['animation', 'display_highlights']:
      if not p in presets:
        presets.append( p )
    
    if len(list(self.volumes.keys())) == 0:
      side_display = False
    
    return render_threejsbrain(
      geoms = geoms,
      start_zoom = start_zoom, font_scale = font_scale,
      background = background, side_canvas = side_canvas, 
      side_width = side_width, side_shift = side_shift, 
      side_display = side_display, control_panel = control_panel, 
      control_display = control_display, 
      default_colormap = default_colormap,
      palettes = palettes, control_presets = presets, coords=coords,
      value_alias = value_alias,
      value_ranges = value_ranges, controllers = controllers, 
      start_server = start_server, **kwargs
    )
  
  def __str__(self):
    s = '''
    Brain - %s
      Surfaces: %s
      Volumes:  %s
    ''' % (
      self.subject_code, 
      ', '.join(list(self.surfaces.keys())),
      ', '.join(list(self.volumes.keys())),
    )
    return s.strip()
  
  @property
  def subject_code(self):
    return self._subject_code
  
  @property
  def vox2vox_MNI305(self):
    mat = matmult4x4(
      matmult4x4(self._xfm, self._Norig),
      inv4x4( self._Torig )
    )
    return [[mat[j+i*4] for j in range(4)] for i in range(4)]
  
  @property
  def scanner_center(self):
    # RAS - 0,0,0
    # inv(Torig) * RAS_origin -> RAS origin in FS space
    # Norig * inv(Torig) * RAS_origin -> RAS origin in scanner space
    #
    # It's the same as the following transform
    # (self$Torig %*% solve( self$Norig ) %*% c(0,0,0,1))[1:3]
    
    re = matmult4x4( self._Norig, inv4x4( self._Torig) )
    return [-re[3], -re[7], -re[11]]

    
  @property
  def surface_types(self):
    return list(self.surfaces.keys())
  
  @property
  def surface_mesh_types(self):
    return dict(
      [(k, v.mesh_type) for k, v in self.surface_types.items()])
  
  @property
  def volume_types(self):
    return list(self.volumes.keys())
  
  @property
  def global_data(self):
    return as_dict({
      self.subject_code : {
        'Norig' : self.Norig,
        'Torig' : self.Torig,
        'xfm' : self.xfm,
        'vox2vox_MNI305' : self.vox2vox_MNI305,
        'scanner_center' : self.scanner_center
      }
    })
  


class BrainVolume:
  def __init__(self, subject_code, volume_type, volume, position=None):
    self.subject_code = None
    volume.layer = set([13])
    self._object = volume
    self.group = volume.group
    self.volume_type = volume_type
    self.set_subject_code( subject_code )
    if position is not None:
      self.set_group_position( position )
    
  def set_subject_code(self, subject_code):
    if self.has_volume:
      self._object.subject_code = subject_code
      self.group.subject_code = subject_code
      self._object.name = '%s (%s)' % (self.volume_type, subject_code)
      self.group.name = "Volume - %s (%s)" % (
        self.volume_type, subject_code
      )
    self.subject_code = subject_code
  
  def set_group_position(self, *args):
    pos = []
    for v in args:
      if isinstance(v, list):
        pos.extend( v )
      else:
        pos.append( v )
    stopifnot(len(pos) == 3, msg='Position must have length 3')
    self.group.position[0] = pos[0]
    self.group.position[1] = pos[1]
    self.group.position[2] = pos[2]
  
  def __str__(self):
    return '''Subject\t\t: %s\nVolume type\t: %s''' % (
      self.subject_code,
      self.volume_type
    )
  
  @property
  def has_volume(self):
    if self._object is None:
      return False
    if isinstance(self._object, DataCubeGeom):
      return True
    return False

class BrainSurface:
  
  def __init__(self, subject_code, surface_type, mesh_type, 
    left_hemisphere, right_hemisphere, position = None):
    
    stopifnot(mesh_type in ['fs', 'std.141'],
      msg = 'We only support SUMA standard 141 or FreeSurfer brain')
    
    left_hemisphere.hemisphere = 'left'
    left_hemisphere.surface_type = surface_type
    left_hemisphere.layer = set([8])
    self.left_hemisphere = left_hemisphere
    
    right_hemisphere.hemisphere = 'right'
    right_hemisphere.surface_type = surface_type
    right_hemisphere.layer = set([8])
    self.right_hemisphere = right_hemisphere
    
    if left_hemisphere.group != right_hemisphere.group:
      # merge right hemisphere to left
      for nm, re in right_hemisphere.group.group_data.items():
        left_hemisphere.group.group_data[ nm ] = re
      right_hemisphere.group = left_hemisphere.group
    
    self.group = left_hemisphere.group
    self.surface_type = surface_type
    self.mesh_type = mesh_type
    self.set_subject_code( subject_code )
    
    if position is not None and len(position) == 3:
      self.set_group_position( position )
  
  def __str__(self):
    return '''Subject\t\t: %s
Surface type\t: %s
Mesh type\t: %s''' % (
      self.subject_code,
      self.surface_type,
      self.mesh_type
    )
  
  def set_subject_code(self, subject_code):
    if self.has_hemispheres:
      self.left_hemisphere.subject_code = subject_code
      self.right_hemisphere.subject_code = subject_code
      self.group.subject_code = subject_code
      
      if self.mesh_type == 'std.141':
        self.left_hemisphere.name = "%s - %s (%s)" % (
          'Standard 141 Left Hemisphere',
          self.surface_type, subject_code
        )
        
        self.right_hemisphere.name = "%s - %s (%s)" % (
          'Standard 141 Right Hemisphere',
          self.surface_type, subject_code
        )
      else:
        self.left_hemisphere.name = "%s - %s (%s)" % (
          'FreeSurfer Left Hemisphere',
          self.surface_type, subject_code
        )
        
        self.right_hemisphere.name = "%s - %s (%s)" % (
          'FreeSurfer Right Hemisphere',
          self.surface_type, subject_code
        )
      self.group.name = "Surface - %s (%s)" % (
        self.surface_type, subject_code
      )
    self.subject_code = subject_code
    pass
  
  def set_group_position(self, *args):
    pos = []
    for x in args:
      if isinstance(x, list):
        pos.extend(x)
      else:
        pos.append(x)
    stopifnot(len(pos) == 3, msg='Position must have length 3')
    self.group.position[0] = pos[0]
    self.group.position[1] = pos[1]
    self.group.position[2] = pos[2]
  
  @property
  def has_hemispheres(self):
    valid = [False, False]
    if self.left_hemisphere is not None and isinstance(self.left_hemisphere, FreeGeom):
      valid[0] = True
    if self.right_hemisphere is not None and isinstance(self.right_hemisphere, FreeGeom):
      valid[1] = True
    return all(valid)

