import unittest
import CUBRIDdb
import locale   
import time     
from xml.dom import minidom

class ExecuteTriggerTest(unittest.TestCase):
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
                self.cursor.execute("drop class if exists hi")
                self.cursor.execute("drop class if exists tt1")
                self.cursor.execute("create class hi ( a int , b string )")
                self.cursor.execute("create class tt1( a int, b string )")

        def tearDown(self):
                self.cursor.close()
                self.conn.close()

        def test_trigger(self):
                print "create trigger !"
                self.cursor.execute("create trigger tt1_insert after insert on tt1 execute insert into hi(a, b) values( obj.a ,to_char(obj.a))")

                self.cursor.execute("insert into tt1(a,b) values(1, 'test')") 
                self.cursor.execute("select * from hi")
                self.row_sl=self.cursor.fetchall()
                for self.value in self.row_sl:
                   print (self.value[0],self.value[1])
                   self.assertEqual(self.value[0],1)
                   self.assertEqual(self.value[1],'1')

                self.cursor.execute("select * from tt1")
                self.row_sl=self.cursor.fetchall()
                for self.value in self.row_sl:
                   print (self.value[0],self.value[1])
                   self.assertEqual(self.value[0],1)
                   self.assertEqual(self.value[1],'test')

                

if __name__ == '__main__':
        suite = unittest.TestLoader().loadTestsFromTestCase(ExecuteTriggerTest)
        unittest.TextTestRunner(verbosity=2).run(suite)
         
