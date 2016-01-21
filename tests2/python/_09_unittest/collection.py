import unittest
import _cubrid
from _cubrid import *
import time
from xml.dom import minidom

class CubridTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
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
        con =_cubrid.connect(conStr, "dba","")
        cur=con.cursor()
        try:
           cur.prepare("drop table if exists collection_tb")
           cur.execute()
           cur.prepare("create table collection_tb( a set of int, b multiset of int , c list of int )")
           cur.execute()
           cur.prepare("insert into collection_tb values( {},{},{}),(null,null,null),( {1,1},{1,1},{1,1}),({1,2,3},{1,2,3},{1,2,3}),( {-1,-2,-3},{-1,-2,-3},{-1,-2,-3})")
           cur.execute()
           cur.prepare("select * from collection_tb where a seteq {'1'} order by 1,2")
           cur.execute()
           row=cur.fetch_row()
           while row:
              print ("row value: ", row)
              row=cur.fetch_row()
        except Exception,e:
              errorValue=str(e)
              print("errorValue: ",errorValue)
        finally:
           cur.close()
           con.close()   

    def test_lob_null(self):
        xmlt = minidom.parse('configuration/python_config.xml')
        ips = xmlt.childNodes[0].getElementsByTagName('ip')
        ip = ips[0].childNodes[0].toxml()
        ports = xmlt.childNodes[0].getElementsByTagName('port')
        port = ports[0].childNodes[0].toxml()
        dbnames = xmlt.childNodes[0].getElementsByTagName('dbname')
        dbname = dbnames[0].childNodes[0].toxml()
        conStr = "CUBRID:"+ip+":"+port+":"+dbname+":::"
        con =_cubrid.connect(conStr, "dba","")
        cur=con.cursor()
        try:
           cur.prepare("drop table if exists collection_tb")
           cur.execute()
           cur.prepare("create table collection_tb( a set of int, b multiset of int , c list of int )")
           cur.execute()
           cur.prepare("insert into collection_tb values({},{},{}),(null,null,null),( {1,1},{1,1},{1,1})")
           cur.execute()
           cur.prepare("select * from collection_tb where a seteq {'1'} order by 1,2")
           cur.execute()
           row=cur.fetch_row()
           print ("row value: ", row)
           row=cur.fetch_row()
           print ("row value: ", row)
           row=cur.fetch_row()
           print ("row value: ", row)
        except Exception,e:
              errorValue=str(e)
              print("errorValue: ",errorValue)
        finally:
           cur.close()
           con.close()
if __name__ == '__main__':
    #unittest.main(defaultTest = 'suite')
    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(CubridTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

