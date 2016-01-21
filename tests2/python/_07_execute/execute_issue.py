import unittest
import CUBRIDdb
import datetime
import locale
import sys
from xml.dom import minidom

class IssueTest(unittest.TestCase):
        def getConStr(self):
                xmlt = minidom.parse('configuration/python_config.xml')
                ips = xmlt.childNodes[0].getElementsByTagName('ip')
                ip = ips[0].childNodes[0].toxml()
                ports = xmlt.childNodes[0].getElementsByTagName('port')
                port = ports[0].childNodes[0].toxml()
                dbnames = xmlt.childNodes[0].getElementsByTagName('dbname')
                dbname = dbnames[0].childNodes[0].toxml()
                conStr = "CUBRID:"+ip+":"+port+":"+dbname+":::"
                return conStr

        def setUp(self):
                conStr = self.getConStr()                
                self.con = CUBRIDdb.connect(conStr, "dba","")
                self.cur = self.con.cursor()
                self.cur.execute("DROP TABLE IF EXISTS issue")
                self.cur.execute("CREATE TABLE issue(nameid int primary key ,age int,name VARCHAR(40))")
                self.cur.execute("INSERT INTO issue (name,nameid,age) VALUES('Mike',1,30),('John',2,28),('Bill',3,45)")

        def tearDown(self):
                self.cur.close()
                self.con.close()

        def test_connect(self):
                print "\nconnect url is empty"
                try:
                    self.con = CUBRIDdb.connect("")
                except Exception,e:
                    errorValue=str(e)
                    print errorValue
                    self.assertEquals(errorValue,"(-20030, 'ERROR: CCI, -20030, Invalid url string')")

                try:
                    self.con = CUBRIDdb.connect()
                except Exception,e:
                    errorValue=str(e)
                    print errorValue
                    self.assertEquals(errorValue,"Required argument 'url' (pos 1) not found")

        def test_execute(self):
                print "\nexecute error statement"
                try:
                    self.cur.execute("error information")
                except Exception,e:
                    errorValue=str(e)
                    print errorValue
                    self.assertEquals(errorValue[1:5],'-493')

                print "\nexecute empty statement"
                try:
                    self.cur.execute()
                except Exception,e:
                    errorValue=str(e)
                    print errorValue
                    self.assertEquals(errorValue,"execute() takes at least 2 arguments (1 given)")
                try:
                    self.cur.execute("")
                except Exception,e:
                    errorValue=str(e)
                    print errorValue
                    self.assertEquals(errorValue[1:5],"-424")

                print "\ncol_count==0"
                try:
                    self.cur.execute("create table nocolumn()")
                except Exception,e:
                    errorValue=str(e)
                    print errorValue
                    self.assertEquals(errorValue[1:5],'-493')
                try:
                    self.cur.execute("select from issue")
                except Exception,e:
                    errorValue=str(e)
                    print errorValue
                    self.assertEquals(errorValue[1:5],'-493')

        def test_executeParam(self):
                print "\nparameter_count==0"
                try:
                    self.cur.execute("insert into issue values()",(1,58,'aaaa'))
                except Exception,e:
                    errorValue=str(e)
                    print errorValue
                    self.assertEquals(errorValue,"(-30014, 'ERROR: CLIENT, -30014, Some parameter not binded')")

                print "\nparameter's index<1 or index>bind_num"
                try:
                    self.cur.execute("insert into issue(nameid,age) values(?,?,?)",(1,58))
                except Exception,e:
                    errorValue=str(e)
                    print errorValue
                    self.assertEquals(errorValue[1:5],'-494')                   

                print "\nparameter's value is not corret"
                try:
                    self.cur.execute("insert into issue values(?,?,?)",(8,'58aaa','aaaa'))
                except Exception,e:
                    errorValue=str(e)
                    print errorValue
                    self.assertEquals(errorValue[1:5],'-494') 
        def test_(self):
                print "\nparameter_count==0"
                try:
                    self.cur.execute("insert into issue values()",(1,58,'aaaa'))
                except Exception,e:
                    errorValue=str(e)
                    print errorValue
                    self.assertEquals(errorValue,"(-30014, 'ERROR: CLIENT, -30014, Some parameter not binded')")

if __name__ == '__main__':
	#suite = unittest.TestLoader().loadTestsFromTestCase(IssueTest)
	#unittest.TextTestRunner(verbosity=2).run(suite)
        suite = unittest.TestSuite()
        if len(sys.argv) == 1:
            suite = unittest.TestLoader().loadTestsFromTestCase(IssueTest)
        else:
            for test_name in sys.argv[1:]:
                suite.addTest(IssueTest(test_name))
        unittest.TextTestRunner(verbosity=2).run(suite)
