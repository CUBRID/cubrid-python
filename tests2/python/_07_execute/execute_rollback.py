import unittest
import CUBRIDdb
import datetime
import locale
from xml.dom import minidom

class RollbackTest(unittest.TestCase):
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
                self.con.set_autocommit(False)
                self.assertEqual(self.con.get_autocommit(), False, "autocommit is off")
                self.cur.execute("DROP TABLE IF EXISTS issue")
                self.cur.execute("CREATE TABLE issue(nameid int primary key ,age int,name VARCHAR(40))")
                self.cur.execute("INSERT INTO issue (name,nameid,age) VALUES('Mike',1,30),('John',2,28),('Bill',3,45)")
                self.con.commit()
        def tearDown(self):
                self.cur.close()
                self.con.close()

        def test_01rollback(self):
                print "\nstatement is right"
                self.cur.execute("INSERT INTO issue (name,nameid,age) VALUES('forrollback',6,66)")
                self.cur.execute("select * from issue where nameid=6")
                self.value=self.cur.fetchone()
                print("before rollback: ",self.value[0],self.value[1],self.value[2])
                self.assertEquals(self.value[1],66)
                
                print "\nrollback"
                self.con.rollback()
                self.cur.execute("select * from issue where nameid=6")
                rows = self.cur.fetchall()
                #print("after rollback: ",self.value[0],self.value[1],self.value[2])
                self.assertEquals(len(rows),0)
                  
        '''
        #error test will execute in "python/_12_autocommit/test_auocommit_01.py_AutocommitTest.test_03errorRollback "
        def test_02errorRollback(self):
                print "\nrollback is not correct "
                self.cur.execute("INSERT INTO issue (name,nameid,age) VALUES('forrollback',6,66)")
                try:
                   self.con.rollback("pass a parameter")
                except Exception,e:
                   errorValue=str(e)
                   print errorValue
                   self.assertEquals(errorValue,"rollback() takes exactly 1 argument (2 given)")
       '''

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(RollbackTest)
	unittest.TextTestRunner(verbosity=2).run(suite)
