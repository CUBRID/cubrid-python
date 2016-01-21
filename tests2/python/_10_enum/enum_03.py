import unittest
import CUBRIDdb
import locale   
import time 
import sys    
from xml.dom import minidom

class Enum03Test(unittest.TestCase):
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
                self.conn = CUBRIDdb.connect(conStr, 'dba','')
		self.cursor= self.conn.cursor()
                nsql='drop table if exists enum03'
                self.cursor.execute(nsql)
                nsql2="create class enum03(i INT, working_days ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'), answers ENUM('Yes', 'No', 'Cancel'))"
                self.cursor.execute(nsql2)
                
        def tearDown(self):
                self.cursor.close()
                self.conn.close()
                
        def test_01selectVersion(self):
                print "normal select version" 
                self.cursor.execute("SELECT VERSION()")
                self.row=self.cursor.fetchone ()
                c=self.row[0]
                print c
                #self.assertEquals(c,'8.4.1.0559')
                
        def test_02insert(self):
                print "enum type insert!" 
                nsql3="insert into enum03 values(1,1,1),(2,'Tuesday','No'), (3, 'Wednesday','Cancel')"
                c3=self.cursor.execute(nsql3)
                self.assertEquals(c3,3)
                self.conn.commit()

        def test_03update(self):
                print "update value"
                nsql3="insert into enum03 values(1,1,1),(2,'Tuesday','No'), (3, 'Wednesday','Cancel')"
                c3=self.cursor.execute(nsql3)
                self.assertEquals(c3,3)
                nsql4="update enum03 set answers=1"
                c4=self.cursor.execute(nsql4)
                self.assertEquals(c4,3)
                
        def test_04select(self):
                print "normal select !"
                nsql4 = "select count(*) from enum03"
                self.cursor.execute(nsql4)
                self.row_sl=self.cursor.fetchone ()
                c_sl=self.row_sl[0]
                self.assertEqual(c_sl,0)
                self.conn.commit()

if __name__ == '__main__':
        suite = unittest.TestSuite()  
        if len(sys.argv) == 1:  
            suite = unittest.TestLoader().loadTestsFromTestCase(Enum03Test)  
        else:  
            for test_name in sys.argv[1:]:  
                suite.addTest(Enum03Test(test_name))  
        unittest.TextTestRunner(verbosity=2).run(suite) 
