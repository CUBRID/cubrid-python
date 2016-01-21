import unittest
import sys
import os
import re
import imp
import string


global modname, classname
def importModule():
        print "\n"
        for root, dirs, files in os.walk(os.path.abspath(os.curdir), True):
            for name in dirs:
                #print os.path.join(root, name)
                sys.path.append(os.path.abspath(name))
            for name in files:
                if os.path.splitext(name)[1] == '.py':
                    modname=os.path.splitext(name)[0]
                    print os.path.join(root, name)
                    #print "import: "+os.path.splitext(name)[0]
                    __import__(modname)
                    mod = sys.modules[modname]
                    for classname in dir(mod):
                        pattern = re.compile(r'.*Test')
                        match = pattern.match(classname)
                        if match: 
                            __import__(modname)
                            #print "modname: "+modname
                            #print "clsname: "+classname
                            aMod = sys.modules[modname]
                            aClass= getattr(aMod, classname)
                            #_temp= __import__(modname+"."+classname,fromlist=[aMod])
                            #from aMod import aClass
                            #suite = unittest.TestSuite()
                            suite = unittest.TestLoader().loadTestsFromTestCase(aClass)
                            unittest.TextTestRunner(verbosity=2).run(suite)
                            print "------------------------------------------------------" 


def runCases():
        suite = unittest.TestSuite()
        if len(sys.argv) == 1:
            suite = unittest.TestLoader().loadTestsFromTestCase(Enum01Test)
        else:
            for test_name in sys.argv[1:]:
                suite.addTest(Enum01Test(test_name))
        unittest.TextTestRunner(verbosity=2).run(suite) 

if __name__ == '__main__':
        importModule()
        #print sys.path
        #runCases()
