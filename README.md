        CUBRID-Python driver for CUBRID
------------------------------------------------------------------------------------------

Overview
========
```
CUBRIDdb driver: CUBRID Module for Python DB API 2.0
                 Python driver for CUBRID Database
Django_cubrid backend: Django backend for CUBRID Database
Author: Li Jinhu (beagem@nhn.com), Li Lin(aniterle@nhn.com), Zhang Hui
Date: December, 2012
```

        Notes about CUBRIDdb driver

Abstract
========
  CUBRIDdb is a Python extension package that implements Python Database API 2.0.
  In additional to the minimal feature set of the standard Python DB API, 
  CUBRID Python API also exposes nearly the entire native client API of the 
  database engine in _cubrid.


Project URL
-----------
  * Project Home: https://github.com/CUBRID/cubrid-python
  * Latest CUBRID Python Driver: http://ftp.cubrid.org/CUBRID_Drivers/Python_Driver/

Dependencies for CUBRIDdb
-------------------------
```
  * CUBRID: 8.4.0 or higher
  * OS    : Windows (x86 and x86_64)
            Linux (32bit and 64bit)
            Other Unix and Unix-like os
  * Python: Python 3.0+
  * Compiler: to build from Source
            Visual Studio 2015 (Windows)
            GNU Developer Toolset 6 or higher
```

Install for CUBRIDdb
--------------------
  To build and install from source, you should move into the top-level directory 
  of the CUBRIDdb distribution and issue the following commands.
 ``` 
  $ git clone --recursive git@github.com:CUBRID/cubrid-python.git
  $ cd cubrid-python
  $ python setup.py build
  $ sudo python setup.py install   (Windows: python setup.py install)
```
Documents
---------
  * See Python DB API 2.0 Spec (http://www.python.org/dev/peps/pep-0249/)
 
Samples
-------
  * See directory "samples".


        Notes about Django_cubrid backend

Notes
-----
 * Django_cubrid is the Django backend for CUBRID Database.
 * Please refer to README_django_cubrid for more information.
