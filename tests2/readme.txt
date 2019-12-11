# This document is a manual that describe how to test function, memoryleak and performance of python interface of CUBRID

* 'valgrind' is required to run this version of test
* python to be run could be selected by arguments
* Python 3.x is not supported

1 Function Test including MemoryLeak (one of the following example)
  1.1 sh runtest.sh
  1.2 sh runtest.sh python=/usr/local/bin/python
  1.3 sh runtest.sh python=/home/python26/bin/python
  * test results can be found in ./function_result

2 Performance Test
  3.1 edit 'runtest.sh' change near line 8, shell variable 'TC_DIR' as follow
      TC_DIR="python"
      TC_DIR="python performance"
  3.2 run perormance test
      $ sh runtest.sh (or sh runtest.sh python=/home/python26/python/bin/python)
      or
      $ cd ./performance;python perf_4_python.py > perf.log
