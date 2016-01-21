import unittest
import CUBRIDdb
import time
import sys
import decimal
import datetime
import locale
from xml.dom import minidom

class AutocommitTest(unittest.TestCase):
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
                self.assertEqual(self.con.get_autocommit(), True, "autocommit defaule is ON")
                self.con.set_autocommit(False)
                self.cur.execute("DROP TABLE IF EXISTS autocommit_t")
                self.cur.execute("CREATE TABLE autocommit_t(nameid int primary key ,age int,name VARCHAR(40))")
                self.con.commit()
        def tearDown(self):
                self.cur.close
                self.con.close

        def test_01autocommit(self):
                self.con.set_autocommit(False)
                self.assertEqual(self.con.get_autocommit(), False, "autocommit is off")
                
                self.cur.execute("insert into autocommit_t(name,nameid,age) values ('Mike',1,30),('John',2,28),('Bill',3,45)" )
                self.con.rollback()
                self.cur.execute("select * from autocommit_t")
                rows = self.cur.fetchall() 
                print "\n"        
                print len(rows)  
                #APIS-469  
                self.assertEqual(len(rows), 0, "0 lines affected")
                self.con.commit()
                rows = self.cur.fetchall()
                print len(rows)
                self.assertEqual(len(rows), 0, "0 lines affected")
                    
                self.con.set_autocommit(True)
                self.assertEqual(self.con.get_autocommit(), True, "autocommit is on")
                
                self.cur.execute("insert into autocommit_t (name,nameid,age) values ('Mike',1,30),('John',2,28),('Bill',3,45)")  #APIS-470
                self.cur.execute("select * from autocommit_t")
                rows = self.cur.fetchall()
                self.assertEqual(len(rows), 3, "3 lines affected");
                
        def test_02rollback(self):
                print "\nstatement is right"
                xddl1 = "drop table if exists autocommit_t"
                self.cur.execute(xddl1)
                ddl1 = "create table autocommit_t (nameid int primary key ,age int,name VARCHAR(40))"
                self.cur.execute(ddl1)
                self.con.set_autocommit(False)
                self.assertEqual(self.con.get_autocommit(), False, "autocommit is off")
                self.cur.execute("INSERT INTO autocommit_t (name,nameid,age) VALUES('forrollback',6,66)")
                self.cur.execute("select * from autocommit_t ")
                rows = self.cur.fetchall()
                print len(rows)
                self.assertEqual(len(rows), 1, "1 lines affected");
                
                print "\nrollback"
                self.con.rollback()
                self.cur.execute("select * from autocommit_t ")
                rows = self.cur.fetchall()
                print len(rows)
                #APIS-469
                self.assertEqual(len(rows), 0, "0 lines affected");
                self.con.commit()
        def test_03errorRollback(self):
                print "\nset_autocommit is not correct "
                self.con.commit()
                self.con.set_autocommit(False)
                print self.con.get_autocommit()
                #APIS-471
#               self.assertEqual(self.con.get_autocommit(), False, "autocommit is off")
                try: 
                   self.con.set_autocommit('ON')                 
                except Exception,e:
                   errorValue=str(e)
                   print errorValue
                   self.assertEquals(errorValue,"Parameter should be a boolean value")

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(AutocommitTest)
	unittest.TextTestRunner(verbosity=2).run(suite)
