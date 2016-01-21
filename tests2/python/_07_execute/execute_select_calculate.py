import unittest
import CUBRIDdb
import locale   
import time     
from xml.dom import minidom

class ExecuteSelectCalculateTest(unittest.TestCase):
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
                self.conn = CUBRIDdb.connect(conStr, "dba","")
		self.cursor= self.conn.cursor()
                dropSql='drop table if exists nonormal_tb'
                self.cursor.execute(dropSql)
                createSql='CREATE TABLE nonormal_tb(nameid int primary key ,name VARCHAR(40))'
                self.cursor.execute(createSql)
                insertSql="INSERT INTO nonormal_tb (name,nameid) VALUES('Mike',1),('John',2),('Bill',3)"
                self.cursor.execute(insertSql)
                
        def tearDown(self):
                self.cursor.close()
                self.conn.close()
                
        def test_select(self):
                print " Name in 'John'  select: " 
                self.cursor.execute("SELECT * FROM ( SELECT * FROM nonormal_tb ) WHERE Name in ('John')")
                self.row=self.cursor.fetchone ()
                print(self.row[0],self.row[1])
                value=self.row[0]
                self.assertEquals(value,2)

                print "SELECT 4 + '5.2': "
                self.cursor.execute("SELECT 4 + '5.2'")
                self.row=self.cursor.fetchone ()
                print(self.row[0])
                value=self.row[0]
                self.assertEquals(value,9.1999999999999993)


                print "select date'2001-02-03' - datetime'2001-02-02 12:00:00 am' "
                self.cursor.execute("select date'2001-02-03' - datetime'2001-02-02 12:00:00 am'")
                self.row=self.cursor.fetchone ()
                print(self.row[0])
                value=self.row[0]
                self.assertEquals(value,'86400000')


                print "SELECT date'2002-01-01' + '10' "
                self.cursor.execute("SELECT date'2002-01-01' + '10'")
                self.row=self.cursor.fetchone ()
                print(self.row[0])
                value=self.row[0]
                #http://jira.cubrid.org/browse/APIS-410
                #self.assertEquals(value,'2002-01-11')


                print "SELECT '1'+'1' "
                self.cursor.execute("SELECT '1'+'1'")
                self.row=self.cursor.fetchone ()
                print(self.row[0])
                value=self.row[0]
                self.assertEquals(value,'11')


                print "SELECT '3'*'2'"
                self.cursor.execute("SELECT '3'*'2'")
                self.row=self.cursor.fetchone ()
                print(self.row[0])
                value=self.row[0]
                self.assertEquals(value,6.0000000000000000)

                print "select BIT_LENGTH('CUBRID'"
                self.cursor.execute("select BIT_LENGTH('CUBRID')")
                self.row=self.cursor.fetchone ()
                print(self.row[0])
                value=self.row[0]
                self.assertEquals(value,48)

                print "select BIT_LENGTH(B'010101010');"
                self.cursor.execute("select BIT_LENGTH(B'010101010')")
                self.row=self.cursor.fetchone ()
                print(self.row[0])
                value=self.row[0]
                self.assertEquals(value,9)

                print "SELECT LENGTH('')"
                self.cursor.execute("SELECT LENGTH('')")
                self.row=self.cursor.fetchone ()
                print(self.row[0])
                value=self.row[0]
                self.assertEquals(value,0)

                print "SELECT CHR(68) || CHR(68-2)"
                self.cursor.execute("SELECT CHR(68) || CHR(68-2)")
                self.row=self.cursor.fetchone ()
                print(self.row[0])
                value=self.row[0]
                self.assertEquals(value,'DB')


                print "SELECT INSTR ('12345abcdeabcde','b', -1)"
                self.cursor.execute("SELECT INSTR ('12345abcdeabcde','b', -1)")
                self.row=self.cursor.fetchone ()
                print(self.row[0])
                value=self.row[0]
                self.assertEquals(value,12)


if __name__ == '__main__':
        suite = unittest.TestLoader().loadTestsFromTestCase(ExecuteSelectCalculateTest)
        unittest.TextTestRunner(verbosity=2).run(suite)
         
