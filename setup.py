#!/usr/bin/env python
from distutils.core import setup
exec(open('fluenpy/version.py').read())

setup(name="fluenpy",
      version=__version__,
      packages=['fluenpy', 'fluenpy.plugins'],
      scripts=['scripts/fluen.py'],
      )
