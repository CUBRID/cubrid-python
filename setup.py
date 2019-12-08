import os
import sys

from distutils import msvc9compiler
msvc9compiler.VERSION = 14.0 #Visual studio 2015

if sys.version > '3':
    setup_file = "setup_3.py"
else:
    setup_file = "setup_2.py"

version = "10.2.0.0001"

#os.system(setup_file)
setup_fh = open(setup_file)
setup_content = setup_fh.read()
setup_fh.close()
exec(setup_content)
