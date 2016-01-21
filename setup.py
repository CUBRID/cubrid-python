import os
import sys

if sys.version > '3':
    setup_file = "setup_3.py"
else:
    setup_file = "setup_2.py"

version = "9.3.0.0002"

#os.system(setup_file)
setup_fh = open(setup_file)
setup_content = setup_fh.read()
setup_fh.close()
exec(setup_content)
