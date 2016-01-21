# This document is a manual that describe how to test function, memoryleak and performance of python interface of CUBRID

1 Function Test
  1.1 sh runTest.sh
  1.1 the result can be found in folder ./function_result

2 MemoryLeak Test
  2.1 sh runTest.sh
  2.1 the result can be found in folder ./memoryLeaklog

3 Performance Test
  3.1 config configuration/python_config.xml
  3.2 cd ./performance
  3.3 python perf_4_python.py > perf.log
  3.4 the result can be found in folder ./perf.log
