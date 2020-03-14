#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ravebrainpy.core as c
import ravebrainpy.utils as pu
import ravebrainpy.io as i

i.import_freesurfer(subject_code='YAB', fspath='/Users/beauchamplab/rave_data/data_dir/demo/YAB/fs')

brain = c.Brain(subject_code = 'YAB', path = '/Users/beauchamplab/rave_data/data_dir/demo/YAB/fs/')

brain.render()

import ravebrainpy
ravebrainpy.utils.stop_all_servers()

fspath = '/Users/beauchamplab/rave_data/data_dir/demo/YAB/fs/'
rave_path = '/Users/beauchamplab/rave_data/data_dir/demo/YAB/fs/RAVEpy/'
subject_code = 'YAB'
vertex_color = 'sulc'

brain = c.Brain(subject_code = subject_code, fspath = fspath)

gp = c.GeomGroup(name='Surface - pial (%s)' % subject_code)

cache_path = os.path.join(rave_path, 'YAB_fs_lh_pial.json')
g1 = c.FreeGeom(
  'FreeSurfer Left Hemisphere - pial (%s)' % subject_code, 
  group=gp, cache_file=cache_path)

cache_path = os.path.join(rave_path, 'YAB_fs_rh_pial.json')
g2 = c.FreeGeom(
  'FreeSurfer Right Hemisphere - pial (%s)' % subject_code, 
  group=gp, cache_file=cache_path)

gp.set_group_data(name='curvature', value=vertex_color)

curv_lh = os.path.join(rave_path, 'YAB_fs_lh_sulc.json')
lvert_name = 'Curvature - lh.%s (%s)' % (vertex_color, subject_code)
brain.add_vertex_color(
  name = lvert_name,
  path = curv_lh
)

curv_rh = os.path.join(rave_path, 'YAB_fs_rh_sulc.json')
rvert_name = 'Curvature - rh.%s (%s)' % (vertex_color, subject_code)
brain.add_vertex_color(
  name = rvert_name,
  path = curv_rh
)

surface = c.BrainSurface(subject_code='YAB', surface_type='pial',mesh_type='fs', left_hemisphere=g1, right_hemisphere=g2)
surface.group.set_group_data('default_vertex_lh_%s' % 'pial', lvert_name)
surface.group.set_group_data('default_vertex_rh_%s' % 'pial', rvert_name)
brain.add_surface(surface=surface)

gp = c.GeomGroup(name='Volume - T1 (YAB)')
cache_path = os.path.join(rave_path, 'YAB_t1.json')
v1 = c.DataCubeGeom(name='T1 (YAB)', group=gp, cache_file=cache_path)
volume = c.BrainVolume(subject_code='YAB', volume_type='T1', volume=v1)
brain.add_volume(volume=volume)

brain.render(debug=True)
