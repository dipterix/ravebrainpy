#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
  name='ravebrainpy',
  version='0.0.1',
  description='Python library to visualize FreeSurfer in web browser',
  url='',
  author='Zhengjia Wang',
  author_email='zhengjia.wang@rice.edu',
  license='MIT',
  packages=['ravebrainpy'],
  install_requires=[
    'numpy', 'pandas', 'nibabel'
  ],
  extras_require={
    'with_jupyter' : ['IPython']
  },
  include_package_data=True,
  zip_safe=False,
  test_suite='nose.collector',
  tests_require=['nose'],
)
