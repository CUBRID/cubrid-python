import ConfigParser
import getopt
import os
import platform
import re
import subprocess
import sys
import zipfile

def interagrationtest():
            python = '/home/python/tools/python265/bin/python'
            
            print ''
            print '>>> Intergrationtest for python driver ...'
            print "Using python:", python
            popen = subprocess.Popen([python, 'run-test.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output1 = popen.communicate()[0]
#            print output1
            
#            popen = subprocess.Popen([python, 'test_cubrid.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#            output2 = popen.communicate()[0]
#            print output2
            output = output1 
            
            lines = output.split('\n')
            tests_list = []
            testname = ''
            status = 'pass'
            message = ''
            for line in lines:
#                print line
                # test_fetchone (__main__.DBAPI20Test) ... ok
                m = re.search('^(test_\w+) \((\w+).(\w+)\) \.\.\. (.*)$', line)
                if m:
                    testname = m.group(2) + '.' + m.group(1)
                    print testname
                    print m.group(4)
                    if m.group(4) == 'ok':
                        status = 'pass'
                        message = ''
                    else:
                        status = 'failed'
                        message = testname + ' ' + m.group(3)
                
                    item = [testname, status, message]
                    tests_list.append(item)
                else:
                    pass
                
            if not os.path.exists('log'):
                os.system('mkdir log')
            # change to the format that junit can be parsed. 
#            maj_ver = re.sub('\.', '_', self.major_version)
#            py_ver = re.sub('\.', '', self.python_version)
#            testsuit_name = 'unittest.CUBRID_' + maj_ver + '_' + 'python' + py_ver + '_' + self.os + '_' + self.platform
            testsuit_name = 'intergrationtest.CUBRID'
            generate_test_report(tests_list, 'log/test_results.xml', testsuit_name)
            
def generate_test_report(tests_list, log_file_name, testsuite_name):
        tests_num = len(tests_list)
        print tests_num
        failures = 0
        disabled = 0
        errors = 0

        if testsuite_name is None:
            testsuite_name = 'intergrationtest.CUBRID'

        # items:  testname status message
        for item in tests_list:
            v = item[1]
            if v == 'failed':
                failures = failures + 1
            elif v == 'disabled':
                disabled = disabled + 1
            elif v == 'error':
                errors = errors + 1
            elif v == 'pass':
                pass
                
        fp = open(log_file_name, 'w')
        fp.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fp.write('<testsuites tests="%d" failures="%d" disabled="%d" errors="%d" time="0" name="AllTests">\n' 
                  % (tests_num, failures, disabled, errors))
        fp.write('\t<testsuite name="%s" tests="%d" failures="%d" disable="%d" errors="%d" time="0">\n' 
                  % (testsuite_name, tests_num, failures, disabled, errors))
        for item in tests_list:
            testname = item[0]
#            print testname
            status = item[1]
#            print status
            if len(item) == 2:
                message = None
            else:    
                message = item[2]
            if status == 'pass':
                fp.write('\t\t<testcase name="%s" status="pass" time="0" classname="%s">\n' % (testname, testsuite_name))
                fp.write('\t\t</testcase>\n')
            else:
                fp.write('\t\t<testcase name="%s" status="failed" time="0" classname="%s">\n' % (testname, testsuite_name))
                if message is None or message == '':
                    fp.write('\t\t\t<failure message="%s failed" type=""></failure>\n' % (testname))
                else:
                    fp.write('\t\t\t<failure message="%s" type=""></failure>\n' % (message))
                fp.write('\t\t</testcase>\n')
        fp.write('\t</testsuite>\n')
        fp.write('</testsuites>\n')
        fp.close()
    
    
    
if __name__ == '__main__':
       interagrationtest()  



