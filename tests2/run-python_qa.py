'''
Created on 2013-3-22

@author: user
'''

import os
import sys
import platform
import ConfigParser
import re
import subprocess
import getopt
import zipfile
from xml.dom import minidom
import commands

def qatest():
            print ''
#            python = os.path.join(os.environ["PYTHON_DIR"], 'bin/python')
            print '>>> Qatest for python driver ...'
#            print "Using python:", python
            
            status = 'pass'
            succ_num = 0
            fail_num = 0
            message = ''
            tests_list = []
            failed_list = []
            testname = ''
            itemname = ''
            for root, dirs, files in os.walk("python", True):
                for file in files:
                    if re.match('^.*.py$', file):
                        testname = os.path.join(root, file) 
                        print "python ", testname   
                        popen = subprocess.Popen(["python", testname], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        output = popen.communicate()[0]
                        results = output.split('======================================================================')
                        if len(results) > 1:
                            print testname, ":  some cases in this file failed"
                            for i in range(1, len(results)):
                                lines = results[i].split('----------------------------------------------------------------------')
                                m = re.search('(ERROR|FAIL): (test_\w*) \(__main__.(\w+)\)', lines[0])
                                print lines[0]
                                if m:
                                    itemname = testname+'_'+m.group(3)+"."+m.group(2)
                                    status = 'failed'
                                    fail_num = fail_num + 1                               
                                    failed_list.append(itemname)
                                    print lines[1]
                                    errormsgs = lines[1].split('\n')
                                    message = errormsgs[len(errormsgs)-3] 
                                    print "fail_num: ", fail_num  
                                    item = [itemname, status, message]
                                    tests_list.append(item)                                                                          
                            lines_ok = results[0].split('\n')
                            for line in lines_ok:
                                print line
                                m = re.search('^(test_\w*) \(__main__.(\w+)\) \.\.\. (.*)$', line)
                                if m:
                                    itemname = testname+'_'+m.group(2)+"."+m.group(1)
                                    status = 'pass'
                                    message = 'ok'
                                    item = [itemname, status, message]
                                    index = -1
                                    try:
                                        index = failed_list.index(itemname)
                                    except Exception ,e:
                                        str(e)
                                    if index == -1:
                                        succ_num = succ_num + 1
                                        print "succ_num: ", succ_num
                                        tests_list.append(item)
                        else:
                            print testname, ":  all cases in this file pass"
                            lines_ok = results[0].split('\n')
                            for line in lines_ok:
                                print line
                                m = re.search('^(test_\w*) \(__main__.(\w+)\) \.\.\. (.*)$', line)
                                if m:
                                    itemname = testname+'_'+m.group(2)+"."+m.group(1)
                                    status = 'pass'
                                    succ_num = succ_num + 1
                                    print "succ_num: ", succ_num
                                    message = 'ok'
                                    item = [itemname, status, message]
                                    tests_list.append(item)
            
            print 'python qatest success num: ', succ_num 
            print 'python qatest fail num: ', fail_num    
            print 'tests_list len: ', len(tests_list)
            for failed in failed_list:
                print  "Failed case: ", failed
            
if __name__ == '__main__':
    qatest()
    