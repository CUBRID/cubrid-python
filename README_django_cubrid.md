Django_cubrid tutorial
======================
```
django_cubrid: Django backend for CUBRID Database
Author: Li Jinhu (beagem@nhn.com), Zhang Hui, Li Lin(aniterle@nhn.com)
Date: December, 2012
```

Overview
--------
Django_cubrid is the official Django backend for CUBRID Database.
When using Django web framework with CUBRID database, the django_cubrid
backend should be used.

```
For more information about CUBRID, visit the web site: 
http://www.cubrid.org
```

Prerequisites
-------------
* Python
Being a Python Web framework, Django requires Python. It works with any Python
version from 2.5 to 2.7 (due to backwards incompatibilities in Python 3.0, 
Django does not currently work with Python 3.0).

So, when using django_cubrid, the Python version should be from 2.5 to 2.7.

* Django
The django_cubrid backend requires Django, so the Django should be installed.
Now only supports Django-1.4. 
It's tested in Django-1.4.2.

Build
-----
* When building the CUBRID Python driver, if the Python version meets the prerequisites, 
the django_cubrid will be installed into Python library.


Configure
---------
Configure the DATABASES part in your setting.py like below:
```
    DATABASES = {
        'default': {
            'ENGINE': 'django_cubrid',       # The backend name: django_cubrid
            'NAME': 'demodb',                # CUBRID Database name: ie, demodb
            'USER': 'public',                # User to access CUBRID: ie, public
            'PASSWORD': '',                  # Password to access CUBRID.
            'HOST': '',                      # Set to empty string for localhost.
            'PORT': '33000',                 # Set to empty string for default.
        }
    }
```

Known issues
------------

* The Django sqlflush maybe failed because of the foreign constraints between database
tables.

* After using the Django loaddata command, the insert SQL manipulation in the application
maybe failed, becuse of the auto field.

License
-------

CUBRID is distributed under two licenses, Database engine is under GPL v2 or
later and the APIs are under BSD license.

```
The django_cubrid is under BSD license.
```
