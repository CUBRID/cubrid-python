import unittest
import _cubrid
from _cubrid import *
import time
from xml.dom import minidom

class CubridTest(unittest.TestCase):
    def setUp(self):
        #con = self._connect()
        #cursor=con.cursor()
        pass

    def tearDown(self):
        #cursor.execute("drop class if exists test_date")
        #con.close()
        #cursor.close()
        pass

    def test_lob(self):
        xmlt = minidom.parse('configuration/python_config.xml')
        ips = xmlt.childNodes[0].getElementsByTagName('ip')
        ip = ips[0].childNodes[0].toxml()
        ports = xmlt.childNodes[0].getElementsByTagName('port')
        port = ports[0].childNodes[0].toxml()
        dbnames = xmlt.childNodes[0].getElementsByTagName('dbname')
        dbname = dbnames[0].childNodes[0].toxml()
        conStr = "CUBRID:"+ip+":"+port+":"+dbname+":::"
        con = _cubrid.connect(conStr, "dba","")
        cur=con.cursor()
        lob=con.lob()
        try:
           cur.prepare("drop table if exists lob_tb")
           cur.execute()
           cur.prepare("create table lob_tb(image_id int PRIMARY KEY AUTO_INCREMENT, image BLOB)")
           cur.execute()
           cur.prepare("insert into lob_tb values(NULL,?)")
           #lob=con.lob()
           lob.imports('cubrid_logo.png')
           cur.bind_lob(1,lob)
           cur.execute()
        except Exception,e:
              errorValue=str(e)
              print("errorValue: ",errorValue)
        finally:
           lob.close()
           cur.close()
           con.close()   

if __name__ == '__main__':
    #unittest.main(defaultTest = 'suite')
    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(CubridTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

