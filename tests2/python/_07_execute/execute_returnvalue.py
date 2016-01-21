from xml.dom import minidom
import CUBRIDdb
import datetime
import decimal
import locale
import sys
import time
import unittest

# APIS-386
class ReturnValueTest(unittest.TestCase):
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
                self.cur.execute("DROP TABLE IF EXISTS returnvalue_t")
                self.cur.execute("CREATE TABLE returnvalue_t(nameid int primary key ,age int,name VARCHAR(40))")
        def tearDown(self):
                self.cur.close
                self.con.close
        def test_01autocommit(self):
                return_value = self.cur.execute("select * from returnvalue_t")
                print return_value
                self.assertEqual(return_value, 0, "return value should be 0")  
                self.cur.execute("insert into returnvalue_t(name,nameid,age) values ('Mike',1,30),('John',2,28),('Bill',3,45)" )
                return_value = self.cur.execute("select * from returnvalue_t")
                print return_value
                self.assertEqual(return_value, 3, "return value should be 3")  
                rows = self.cur.fetchall() 
                print len(rows)  
                self.assertEqual(len(rows), 3, "3 lines affected")    

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ReturnValueTest)
    unittest.TextTestRunner(verbosity=2).run(suite)               
                 