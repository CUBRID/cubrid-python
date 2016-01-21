import unittest
import _cubrid
from _cubrid import *
import time
from xml.dom import minidom

class CubridTest(unittest.TestCase):
#this method contain _cubrid_ConnectionObject_repr, _cubrid_ConnectionObject_repr, next_result three methods
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_nextresult(self):
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
           print con
	   print cur
	   cur.prepare("drop table if exists nextResult_tb")
           cur.execute()
           cur.prepare("create table nextResult_tb(id int)")
           cur.execute()
           cur.prepare("insert into nextResult_tb values(1),(2),(3),(4),(5)")
           cur.execute()
           cur.prepare("drop table if exists nextResult_tb2")
           cur.execute()
           cur.prepare("create table nextResult_tb2(id int)")
           cur.execute()
           cur.prepare("insert into nextResult_tb2 values(6),(7),(8),(9),(10)")
           cur.execute()
           cur.prepare("select * from nextResult_tb;select * from nextResult_tb2")
           cur.execute(CUBRID_EXEC_QUERY_ALL)
           cur.next_result()
           row=cur.fetch_row()
           while row:
              print ("row value: ", row)
              row=cur.fetch_row() 
           print row
        except Exception,e:
              errorValue=str(e)
              print("errorValue: ",errorValue)
        finally:
           lob.close()
           cur.close()
           con.close()   
	   print cur
	   print con

if __name__ == '__main__':
    #unittest.main(defaultTest = 'suite')
    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(CubridTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

