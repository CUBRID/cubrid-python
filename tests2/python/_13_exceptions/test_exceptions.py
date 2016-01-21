from xml.dom import minidom
import CUBRIDdb
import datetime
import decimal
import locale
import sys
import time
import unittest

# APIS-368
class ExceptionsTest(unittest.TestCase):
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
                self.cur.execute("DROP TABLE IF EXISTS exceptions_t")
                self.cur.execute("CREATE TABLE exceptions_t(nameid int primary key ,age int,name VARCHAR(40))")
                self.cur.execute("INSERT INTO exceptions_t (name,nameid,age) VALUES('Mike',1,30),('John',2,28),('Bill',3,45)")
        def tearDown(self):
                self.cur.close
                self.con.close
                
      
        def test_01Exceptions(self):
            con =  self.con
            error = 0
            errorValue = ''
            try:
                cur = con.cursor()
                cur.execute("insert into exceptions_t values error_sql('Hello') ")
            except CUBRIDdb.DatabaseError, e:
                error = 1
                errorValue = str(e)
            finally:
                con.close()
            #print >>sys.stderr,  "\nException...Error %d: %s" % (e.args[0], e.args[1])
            self.assertEqual(error, 1, "catch one except.")
            #print "\n", e.args[0]
            #print "\n", errorValue
            self.assertEquals(errorValue,"(-493, \"ERROR: DBMS, -493, Syntax: In line 1, column 33 before \'(\'Hello\') \'\\nSyntax error: unexpected \'error_sql\', expecting \'(\' \")")
             
            error = 0
            errorValue = ''
            try:
                cur = con.cursor()
                cur.fetchone()
                cur.execute("insert into exceptions_t values ('forrollback',6,66, 10) ")
            except CUBRIDdb.Error, e:
                error = 1
                errorValue = str(e)
                #print >>sys.stderr,  "\nException...Error %d: %s" % (e.args[0], e.args[1])
            except Exception,e1:
                print "\n",str(e1)
            self.assertEqual(error, 1, "catch one except. OK.")
            self.assertEquals(errorValue, "(-20002, 'ERROR: CCI, -20002, Invalid connection handle')")
            
        
        def test_02Exceptions(self):
                #print "\nconnect url is empty"
                try:
                    self.con = CUBRIDdb.connect("")
                except CUBRIDdb.InterfaceError ,e:
                    errorValue=str(e)
                    #print errorValue
                    self.assertEquals(errorValue,"(-20030, 'ERROR: CCI, -20030, Invalid url string')")

                try:
                    self.con = CUBRIDdb.connect()
                except Exception ,e:
                    errorValue=str(e)
                    #print errorValue
                    self.assertEquals(errorValue,"Required argument 'url' (pos 1) not found")
            
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ExceptionsTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
