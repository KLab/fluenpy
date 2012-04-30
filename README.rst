fluenpy
=======

install
-------

::

   wget https://github.com/downloads/KLab/fluenpy/fluenpy-bootstrap.py
   python fluenpy-bootstrap.py /path/to/fluenpy


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

