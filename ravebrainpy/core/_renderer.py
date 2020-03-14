#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shutil
import json
import atexit
from ..utils import port_occupied, tempfile, make_parent_dir, make_dirs
from ..utils import open_browser, start_simple_server
from ._group import GeomGroup
from ._keyframe import KeyFrame, ColorMap
from ._geom_abs import AbstractGeom
from ._geom_blank import BlankGeom

# import ravebrainpy
# __file__ = ravebrainpy.core

# import ravebrainpy.core as c
# c.render_threejsbrain(background="#ccff99")


def render_threejsbrain(
  geoms=[], background = "#FFFFFF", font_scale=1, timestamp=True,
  side_canvas=True, side_zoom=1, side_width=250, side_shift=[0,0],
  side_display=True, control_panel=True, control_presets=[],
  control_display=True, camera_center=[0,0,0], camera_pos=[500,0,0],
  start_zoom=1, coords=None, default_colormap=None, palettes={},
  value_ranges={}, value_alias={}, show_inactive_electrodes=True, 
  widget_id="threebrain_data", tmp_dirname=None, debug=False,
  token=None, controllers={}, global_data={}, global_files={},
  start_server=False):
  
  # ------------------------ Data check ---------------------
  if len( camera_center ) != 3:
    raise Exception('camera_center must be a list of length 3')
  
  if coords is not None and len( coords ) != 3:
    raise Exception('coords must be None or a list of length 3')
  
  if len( camera_pos ) != 3:
    raise Exception('camera_pos must be a list of length 3, cannot be origin')
  
  if font_scale <= 0:
    font_scale = 1
  if start_zoom <= 0:
    start_zoom = 1
  
  # --------------------- Generate data ---------------------
  
  # 1. global data
  global_container = BlankGeom(
    name = '__blank__', 
    group = GeomGroup(name = '__global_data'))
  for k, v in global_data.items():
    global_container.group.set_group_data(
      name = '__global_data__%s' % k, value = v)
  for nm, file_info in global_files.items():
    if isinstance(file_info, dict):
      nms = ["path", "absolute_path", "file_name", "is_new_cache", 
              "is_cache"]
      if all([x in file_info for x in nms]):
        global_container.group.set_group_data(
          name = '__global_data__%s' % nm, value = file_info,
          is_cached = True, cache_if_not_exists = False)
  
  # 2. groups
  geoms = list(set(geoms))
  geoms.insert(0, global_container)
  groups = set()
  animation_types = set()
  for geom in geoms:
    if geom.group is not None:
      groups.add( geom.group )
    animation_types.update( geom.animation_types )
  groups = list(groups)
  
  # 3. color
  # get color schema
  pnames = list(palettes.keys())
  animation_types = list(animation_types)
  color_maps = {}
  for atype in animation_types:
    cmap = ColorMap(name = atype, geoms = geoms, 
      alias = value_alias.get(atype, None))
    if atype in pnames:
      cmap.set_colors( palettes[atype] )
    if cmap.value_type == 'continuous':
      vrg = value_ranges.get(atype, [])
      if len(vrg) >= 2:
        cmap.value_range = [vrg[0], vrg[1]]
        if len(vrg) >= 4:
          cmap.hard_range = [vrg[2], vrg[3]]
          if vrg[2] > vrg[3]:
            cmap.hard_range = [vrg[3], vrg[2]]
    color_maps[ atype ] = cmap.to_dict()
  
  if len(animation_types) > 0:
    if default_colormap is None or not default_colormap in animation_types:
      default_colormap = animation_types[0]
  else:
    default_colormap = None
  
  # # Check elements
  geom_dict = [g.to_dict() for g in geoms]
  group_dict = [g.to_dict() for g in groups]
  
  # Generate temporary file
  tmpdir = tempfile(prefix='py3bviewer_')
  
  # Copy Group files
  lib_path = 'lib/'
  data_path = os.path.join( tmpdir, 'lib', '%s-0' % widget_id )
  make_dirs(data_path)
  
  for g in groups:
    if g.cached_items is not None and len(g.cached_items) > 0:
      os.mkdir(os.path.join(data_path, g.cache_name()))
      for f in g.cached_items:
        re = g.group_data[f]
        shutil.copyfile(
          src = re['absolute_path'],
          dst = os.path.join(data_path, g.cache_name(), re['file_name'])
        )
      
  complete_presets = ["subject2","surface_type2","hemisphere_material",
        "map_template","electrodes","animation","display_highlights"]
  for preset in control_presets:
    if complete_presets.index( preset ) < 0:
      complete_presets.append( preset )
  
  # Where libraries are stored
  settings = {
    'side_camera'         : side_canvas,
    'side_canvas_zoom'    : side_zoom,
    'side_canvas_width'   : side_width,
    'side_canvas_shift'   : side_shift,
    'color_maps'          : color_maps,
    'default_colormap'    : default_colormap,
    'hide_controls'       : not control_panel,
    'control_center'      : camera_center,
    'camera_pos'          : camera_pos,
    'font_magnification'  : font_scale,
    'start_zoom'          : start_zoom,
    'show_legend'         : True,
    'render_timestamp'    : timestamp,
    'control_presets'     : control_presets,
    'cache_folder'        : lib_path + widget_id + '-0/',
    'lib_path'            : lib_path,
    'default_controllers' : controllers,
    'debug'               : debug,
    'background'          : background,
    'token'               : token,
    'coords'              : coords,
    'show_inactive_electrodes' : show_inactive_electrodes,
    'side_display'        : side_display,
    'control_display'     : control_display
  }
  
  data = {
    "x":{
      "groups":group_dict, "geoms":geom_dict, "settings": settings
    },"evals":[],"jsHooks":[]
  }
  data_str = json.dumps(data)
  
  
  # move assets to temporary directory
  pkg_dir, pkg_fname = os.path.split(__file__)
  
  # pkg_dir="/Users/beauchamplab/Dropbox/projects/ravebrainpy/ravebrainpy/core"
  asset_dir = os.path.join( os.path.dirname(pkg_dir), 'assets' )
  index_path = os.path.join( os.path.dirname(pkg_dir), 'assets', 'index.html' )
  target_dir = os.path.join( tmpdir, 'lib' )
  target_idx = os.path.join( tmpdir, 'index.html' )
  
  for (a,b,c) in os.walk(asset_dir, topdown=True):
    for fn in c:
      src = os.path.join(a, fn)
      dst = os.path.join(
        target_dir,
        os.path.relpath(path=src, start=asset_dir)
      )
      make_parent_dir(dst)
      shutil.copyfile(src=src, dst=dst)
  
  # shutil.copytree(asset_dir, target_dir, symlinks=False, 
  #   copy_function=shutil.copyfile, dirs_exist_ok=True)
  
  # Generate index.html
  with open(index_path, 'r') as fidx:
    content = fidx.readlines()
  
  content = ''.join(content)
  
  # replace widget ID
  content = content.replace("{{WIDGETID}}", '2434907dasd')
  # add data
  content = content.replace("{{WIDGETDATA}}", data_str)
  
  with open(target_idx, 'w+') as tidx:
    tidx.writelines(content)
  
  if not start_server:
    return tmpdir;
  
  return start_viewer( tmpdir )
  
  


def start_viewer( tempdir, host="127.0.0.1", port=12355 ):
  free_port = port
  for i in range(10000):
    free_port = port + i
    if port_occupied(free_port):
      print('Port %d is in use. Try next port...' % free_port)
    else:
      break
  return start_simple_server(host, free_port, tempdir)
  



