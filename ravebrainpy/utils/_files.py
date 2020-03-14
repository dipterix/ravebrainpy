#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import hashlib
import math
import json
import tempfile as tpf
import atexit


from ._funcs import stopifnot, rand_string, as_dict

def unlink(path, recursive=True):
  removed = True
  if os.path.exists(path):
    removed = False
    if os.path.isfile(path):
      try:
        os.remove(path)
        removed = True
      except Exception as e:
        pass
    elif recursive:
      try:
        os.removedirs(path)
        removed = True
      except Exception as e:
        pass
  return removed

def tempdir(check=False):
  d = os.path.join(tpf.gettempdir(), 'py3jsbrain')
  if check:
    make_dirs(d)
  return normalize_path(d)

  
def tempfile(prefix='file_', ext=''):
  fname = '%s%s%s' % (prefix, rand_string(), ext)
  path = os.path.join(tempdir(), fname)
  atexit.register(unlink, path, False)
  atexit.register(unlink, path, True)
  return path

def make_parent_dir(path):
  path = normalize_path(path)
  dirpath = os.path.dirname(path)
  os.makedirs( dirpath, mode=0o777, exist_ok=True )

def make_dirs(path):
  path = normalize_path(path)
  os.makedirs( path, mode=0o777, exist_ok=True )

def file_exists(path):
  return os.path.exists(path)

def normalize_path(path):
  return os.path.abspath(path)

def digest( data, length = 20 ):
  m = hashlib.shake_128(to_json(data).encode("UTF-8"))
  return m.hexdigest(math.ceil(length / 2))

def digest_file( file, length = 20, mode = 'r' ):
  m = hashlib.shake_128()
  def _update_hash(s):
    if mode == 'r':
      s = s.encode("UTF-8")
    m.update(s)
    return ''
  read_from_file(file, sep='', ifnotfound=None, buf=4096,
    mode=mode, op = _update_hash)
  return m.hexdigest(math.ceil(length / 2))

# # Almost the same speed, but more RAM
# def digest_file2( file, length = 20 ):
#   s = read_from_file(file, sep='')
#   m = hashlib.shake_128(s.encode("UTF-8"))
#   return m.hexdigest(math.ceil(length / 2))

def write_to_file( s, path ):
  make_parent_dir( path )
  with open(path, 'w+', encoding='utf-8') as f:
    f.write( s )
  return None

def read_from_file( path, sep = None, ifnotfound=None, 
  op = None, buf=None, mode='r' ):
  if not os.path.exists(path):
    return ifnotfound
  with open( path, mode ) as f:
    if op is None:
      s = f.readlines()
    else:
      if buf is None:
        s = [op(x) for x in f]
      else:
        # op for each buf
        if mode == 'rb':
          it = iter(lambda: f.read(buf), b"")
        else:
          it = iter(lambda: f.read(buf), "")
        s = [op(chunk) for chunk in it]
  if sep is None:
    return s
  return sep.join(s)


def to_json( x, dataframe = 'row', matrix = 'rowmajor', 
  to_file = None, **kwargs ):
  s = json.dumps(as_dict(x, dataframe=dataframe, matrix=matrix))
  if to_file is not None:
    write_to_file(s, to_file)
  return s

def check_digestfile(path, checksum_file=None, key='digest', **kwargs):
  # path = '/Users/beauchamplab/rave_data/data_dir/demo/YAB/fs/RAVEpy/YAB_t1.json'
  if checksum_file is None:
    checksum_file = path + '.pydigest'
  if not os.path.exists(checksum_file) or not os.path.exists(path):
    return False
  try:
    d = from_json(from_file=checksum_file)
    vold = d['key']
    v = digest_file(path, **kwargs)
    return vold == v
  except Exception as e:
    return False


def json_cache( path, data, recache=False, use_digest=True, 
                digest_header=None, digest_path=None, 
                **kargs ):
  path = normalize_path(path)
  if digest_path is None:
    digest_path = path + '.pydigest'
  digest_content = { 'digest' : 'Nah' }
  rewrite_digest = True
  if use_digest:
    if type(digest_header) is dict:
      digest_content = digest_header.copy()
    
    digest_content['digest'] = digest(data)
    digest_content['header_digest'] = digest(digest_content)
  
  cached_digest = {}
  if recache:
    print('Re-generate cache...')
  
  # check whether previous cache signature is valid
  if not recache and os.path.exists( path ) and use_digest:
    if not os.path.exists( digest_path ):
      recache = True
    else:
      try:
        cached_digest = from_json( digest_path )
        if cached_digest.get('digest', '') != digest_content['digest']:
          recache = True
        else:
          rewrite_digest=False
      except Exception as e:
        recache = True
    if recache:
      print('Digest missing or not match.')
  
  is_new_cache = False
  
  if recache or not os.path.exists( path ):
    print('Creating cache data to - %s' % path)
    s = to_json( data, **kargs )
    # create dir
    make_parent_dir( path )
    #os.makedirs( os.path.dirname(path), exist_ok=True)
    # save to path
    with open(path, 'w+') as f:
      f.write(s)
    is_new_cache=True
  
  if use_digest and rewrite_digest:
    # also check digest_content is changed?
    to_json(digest_content, to_file = digest_path)
  
  return {
    'path'            : path,
    'absolute_path'   : normalize_path(path),
    'file_name'       : os.path.basename(path),
    'is_new_cache'    : is_new_cache,
    'is_cache'        : True
  }

def file_exists( path ):
  return os.path.exists(path)



def from_json(txt=None, from_file=None, **kwargs):
  if from_file is not None:
    stopifnot(txt is None, msg = 
      'Either "txt" or "from_file" must be None')
    stopifnot(file_exists(from_file), msg='from_json: file not found.')
    
    with open(from_file, 'r') as f:
      re = json.load(f)
  else:
    re = json.loads(txt)
  return re
