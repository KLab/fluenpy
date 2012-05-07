#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# load __version__ without importing any other files.
exec(open('fluenpy/version.py').read())

setup(name="fluenpy",
      version=__version__,
      packages=['fluenpy',
                'fluenpy.plugins'
                ],
      scripts=['scripts/fluen.py'],
      install_requires=[
          'msgpack-python',
          'gevent>=1.0b2',
          ]
      )
