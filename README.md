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
  * OS    : Windows (x86_64)
            Linux (64bit)
            Other Unix and Unix-like os
  * Python: Python 2.6+
            Python 3.0 ~ Python 3.6
  * Compiler: to build from Source
            Visual Studio 2017 (For Windows)
            GNU Developer Toolset 8 or higher (For Linux)
            ncurses-devel And python-devel (For Linux)
```

Install for CUBRIDdb
--------------------
  To build and install from source, you should move into the top-level directory 
  of the CUBRIDdb distribution and issue the following commands.

  For Python 3.5 or Lower
  ``` 
  $ git clone --recursive git@github.com:CUBRID/cubrid-python.git
  $ cd cubrid-python
  $ python setup.py build          (Windows: First, must run env_windows.bat.)
  $ sudo python setup.py install   (Windows: python setup.py install)
  ```

  For Python 3.8 or Higher
  ```
  $ git clone --recursive git@github.com:CUBRID/cubrid-python.git
  $ cd cubrid-python
  $ python setup.py bdist_wheel
  $ pip install dist/CUBRID_Python-{DriverVersion}-{Python tag}-{ABI tag}-{Platform tag}.whl
  (On Linux, you may need sudo privileges depending on the python version.)
  ```

  If you can't build using setup.py directly in the future.
  ```
  $ git clone --recursive git@github.com:CUBRID/cubrid-python.git
  $ cd cubrid-python
  $ python -m build -w
  $ pip install dist/CUBRID_Python-{DriverVersion}-{Python tag}-{ABI tag}-{Platform tag}.whl
  (On Linux, you may need sudo privileges depending on the python version.)
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
