* 'valgrind' is required to run memory leak test
* Python 3.x is not supported

```
Usage: runtest.sh [OPTIONS]
 OPTIONS
 -p arg   Set python binary to use
 -m       Run with MemoryLeak Test (valgrind is required)
 -a       Run all TestCases including performance test
```

* examples
```
$ sh runtest.sh
$ sh runtest.sh -m
$ sh runtest.sh -p /home/python26/bin/python
$ sh runtest.sh -a -m -p /usr/local/bin/python
```
