import unittest
import CUBRIDdb
import locale   
import time 
import sys    
from xml.dom import minidom

class Enum02Test(unittest.TestCase):
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
                nsql='drop table if exists enum04'
                self.cursor.execute(nsql)
                nsql2="create class enum04(e1 enum('a', 'b'), e2 enum('Yes', 'No', 'Cancel'))"
                self.cursor.execute(nsql2)
                nsql3="insert into enum04 values (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)"
                c3=self.cursor.execute(nsql3)
                
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
                
        def test_update01(self):
                print "enum update 01!" 
                nsql3="update enum04 set e1=cast(e2 as int) where e2 < 3"
                c3=self.cursor.execute(nsql3)
                self.assertEquals(c3,4)
                self.conn.commit()
                nsql4 = "select * from enum04"
                self.cursor.execute(nsql4)
                results=self.cursor.fetchall()
                for res in results:
                        print(res)
                self.assertEquals(6,len(results))

        def test_update02(self):
                print "enum update 02!"
                nsql4 = "update enum04 set e2=e1 + 1"
                c4=self.cursor.execute(nsql4)
                self.assertEqual(c4,6)
                nsql4 = "select * from enum04"
                self.cursor.execute(nsql4)
                results=self.cursor.fetchall()
                for res in results:
                        print(res)
                self.assertEquals(6,len(results))

        def test_update03(self):
                print "enum update 03"
                nsql4 = "update enum04 set e1='b', e2='No'"
                c4=self.cursor.execute(nsql4)
                self.assertEqual(c4,6)
                nsql4 = "select * from enum04"
                self.cursor.execute(nsql4)
                results=self.cursor.fetchall()
                for res in results:
                        print(res)
                self.assertEquals(6,len(results))

if __name__ == '__main__':
        suite = unittest.TestSuite()  
        if len(sys.argv) == 1:  
            suite = unittest.TestLoader().loadTestsFromTestCase(Enum02Test)  
        else:  
            for test_name in sys.argv[1:]:  
                suite.addTest(Enum02Test(test_name))  
        unittest.TextTestRunner(verbosity=2).run(suite) 
