#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import webbrowser
import http.server
import multiprocessing
import os
import socket
import time
import atexit

def port_occupied(port):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    return s.connect_ex(('localhost', port)) == 0
  return False


class HTTPHandler(http.server.SimpleHTTPRequestHandler):
  """This handler uses server.base_path instead of always using os.getcwd()"""
  def translate_path(self, path):
    path = http.server.SimpleHTTPRequestHandler.translate_path(self, path)
    relpath = os.path.relpath(path, os.getcwd())
    fullpath = os.path.join(self.server.base_path, relpath)
    return fullpath
  def log_message(self, *args, **kwargs):
    pass

class HTTPServer(http.server.HTTPServer):
  """The main server, you pass in base_path which is the path you want to serve requests from"""
  def __init__(self, base_path, server_address, RequestHandlerClass=HTTPHandler):
    self.base_path = base_path
    http.server.HTTPServer.__init__(self, server_address, RequestHandlerClass)


def open_browser(url, protocol='http'):
  webbrowser.open('%s://%s', (protocol, url), new=2)


server_lists = {}
class SimpleServer(multiprocessing.Process):
  def __init__(self, host, port, path):
    super().__init__()
    self.daemon = True
    self.host = host
    self.port = port
    self.path = path
    self._strport = str(port)
    if self._strport in server_lists:
      all_ports = [int(x) for x in list(server_lists.keys())]
      port = max(all_ports) + 1
      port = port_occupied(port)
      self.port = port
      self._strport = str(port)
    server_lists[self._strport] = self
    self.name = 'py-threeBrain-server-%s' % self._strport
    
  def start(self, **kwargs):
    host = self.host
    port = self.port
    path = self.path
    print("serving at \n\thttp://%s:%d" % (host, port))
    print("To stop the server, use\n\t'%s', or \n\t'%s'" % (
      'ravebrainpy.utils.stop_server(%d)' % port,
      'ravebrainpy.utils.stop_all_servers()'
    ))
    super().start(**kwargs)
  
  def run(self):
    host = self.host
    port = self.port
    path = self.path
    with HTTPServer(path, (host, port)) as httpd:
      httpd.serve_forever()
  
  def stop_server(self):
    if self.is_alive():
      try:
        self.terminate()
        server_lists.pop(self._strport, None)
      except Exception as e:
        print('Cannot terminate server at port %d' % self.port)

def detect_jupyter():
  try:
    import IPython
    if IPython.get_ipython() is not None:
      # running in iPython environment
      shell = get_ipython().__class__.__name__
      if shell != 'TerminalInteractiveShell':
        return True
  except Exception as e:
    pass
  
  return False

def start_simple_server(host, port, path, launch_browser=True):
  serv = SimpleServer(host, port, path)
  serv.start()
  atexit.register(stop_server, serv.port)
  # Need time to prepare
  time.sleep(1)
  
  url = 'http://%s:%d' % (serv.host, serv.port)
  if launch_browser:
    if detect_jupyter():
      import IPython
      return IPython.display.IFrame(url, width="100%", height="500")
    else:
      webbrowser.open(url, new=2)
  
  return url
  
  
def stop_server(port):
  port = str(port)
  serv = server_lists.get(port, None)
  if serv is None:
    return 2
  if not serv.is_alive():
    server_lists.pop(port, None)
    return 1
  serv.stop_server()
  return 0

def stop_all_servers():
  for k in list(server_lists.keys()):
    stop_server(k)
  

