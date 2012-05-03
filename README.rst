fluenpy
=======

THIS IS PRE-ALPHA QUALITY.
DON'T USE THIS FOR PRODUCTION ENVIRONMENT.

fluentd_ clone implemented with Python.
It has fewer plugins than fluentd but easy to setup and memory efficient.

.. _fluentd:: http://fluentd.org/


requirements
------------
Python >= 2.6
gevent >= 1.0b2
msgpack-python


install
-------

fleunpy provides bootstrap script. It makes virtual environment for 

::

   wget https://github.com/downloads/KLab/fluenpy/fluenpy-bootstrap.py
   python fluenpy-bootstrap.py /path/to/fluenpy


without bootstrap
^^^^^^^^^^^^^^^^^

Using virtualenv_ is highly recommanded. Installing virtualenv is very easy::

   $ wget https://raw.github.com/pypa/virtualenv/master/virtualenv.py
   $ python virtualenv.py --distribute /path/to/fluenpy
   $ source /path/to/fluenpy/bin/activate
   (fluenpy) $

_virtualenv:: http://pypi.python.org/pypi/virtualenv

To install fluenpy::

   (fluenpy) $ pip install msgpack-python
   (fluenpy) $ pip install http://gevent.googlecode.com/files/gevent-1.0b2.tar.gz
   (fluenpy) $ pip install https://github.com/KLab/fluenpy/tarball/master


upgrade
^^^^^^^

::

   (fluenpy) $ pip install --upgrade https://github.com/KLab/fluenpy/tarball/master


setup
-----

See fluentd document.

sample configuration file::

   # fluent.conf
   <source>
      forward
      port 10000
   </source>
   <source>
      http
      port 8890
   </source>
   <match **>
      type stdout
   </match>

execute
--------

::

   /path/to/fluenpy/bin/fluen.py -c fluent.conf

