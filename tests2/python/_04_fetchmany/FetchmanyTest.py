import unittest
import CUBRIDdb
import time
import locale
from xml.dom import minidom

class FetchmanyTest(unittest.TestCase):
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

                sqlDrop = "drop table if exists tdb"
                self.cur.execute(sqlDrop)
                sqlCreate = "create table tdb(id NUMERIC AUTO_INCREMENT(1, 1), age int, name varchar(50))"
                self.cur.execute(sqlCreate)
		self.rownum = 1000
		for i in range(self.rownum):
                        sqlInsert = "insert into tdb values(1,20,'myName')"
                        self.cur.execute(sqlInsert)

        def tearDown(self):
                sqlDrop = "drop table if exists tdb"
                self.cur.execute(sqlDrop)
                self.cur.close
                self.con.close

        def test_fetchmany_nosize(self):
#               test fetchmany without inputing size
                sqlSelect = "select * from tdb"
                self.cur.execute(sqlSelect)
                data = self.cur.fetchmany()
                self.assertEquals(1, len(data))
		dataCheck=[1,20,'myName']
		self.assertEquals(dataCheck,data[0])

        def test_fetchmany_negativeOne(self):
#               test fetchmany with size = -1
                sqlSelect = "select * from tdb"
                self.cur.execute(sqlSelect)
                data = self.cur.fetchmany(-1)
                self.assertEquals(0, len(data))

        def test_fetchmany_zero(self):
#               test fetchmany with size = 0
                sqlSelect = "select * from tdb"
                self.cur.execute(sqlSelect)
                data = self.cur.fetchmany(0)
                self.assertEquals(0, len(data))

        def test_fetchmany_all(self):
#               test fetchmany with size = self.rownum
                sqlSelect = "select * from tdb"
                self.cur.execute(sqlSelect)
                data = self.cur.fetchmany(self.rownum)
                self.assertEquals(self.rownum, len(data))

        def test_fetchmany_overflow(self):
#               test fetchmany with size = self.rownum + 10
                sqlSelect = "select * from tdb"
                self.cur.execute(sqlSelect)
                data = self.cur.fetchmany(self.rownum+10)
                self.assertEquals(self.rownum, len(data))



if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(FetchmanyTest)
	unittest.TextTestRunner(verbosity=2).run(suite)
