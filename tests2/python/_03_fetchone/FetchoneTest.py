import unittest
import CUBRIDdb
import time
import locale
from xml.dom import minidom

class FetchoneTest(unittest.TestCase):
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
#		self.con = CUBRIDdb.connect("CUBRID:localhost:33012:demodb", "dba","")
                self.cur = self.con.cursor()

                sqlDrop = "drop table if exists tdb"
                self.cur.execute(sqlDrop)
                sqlCreate = "create table tdb(id NUMERIC AUTO_INCREMENT(1, 1), age int, name varchar(50))"
                self.cur.execute(sqlCreate)
                sqlInsert = "insert into tdb values (null,20,'Lily')"
                self.cur.execute(sqlInsert)

        def tearDown(self):
                sqlDrop = "drop table if exists tdb"
                self.cur.execute(sqlDrop)
                self.cur.close
                self.con.close

        def test_fetchone_multi(self):
#               test fetchone more than one time
                sqlInsert = "insert into tdb(age) values(21)"
                self.cur.execute(sqlInsert)
                sqlSelect = "select * from tdb"
                self.cur.execute(sqlSelect)
                data1 = self.cur.fetchone()
                data2 = self.cur.fetchone()
                self.assertEquals(20, data1[1])
                self.assertEquals(21, data2[1])

        def test_fetchone_largeData(self):
#               test fetchone with 10000 records
		dataNum=10000
		for i in range(dataNum):
	                sqlInsert = "insert into tdb values(NULL,21,'myName')"
	                self.cur.execute(sqlInsert)
                sqlSelect = "select * from tdb order by id asc"
                self.cur.execute(sqlSelect)
                for i in range(dataNum):
			data = self.cur.fetchone()
# 		        self.assertEquals(i+1, locale.atoi(data[0]))
		        self.assertEquals(i+1, data[0])

        def test_fetchone_norecord(self):
#               test fetchone when there has no record in table
                sqlDelete = "delete from tdb"
                self.cur.execute(sqlDelete)
                sqlSelect = "select * from tdb"
                self.cur.execute(sqlSelect)
                data = self.cur.fetchone()
                self.assertEquals(None,data)

        def test_fetchone_overflow(self):
#               test fetchone when overflow
                sqlSelect = "select * from tdb"
                self.cur.execute(sqlSelect)
                data1 = self.cur.fetchone()
                data2 = self.cur.fetchone()
                self.assertEquals(None,data2)

        def test_ValidConn(self):
                try:
			self.con1 = CUBRIDdb.connect("CUBRID:localhost:33111:demodb", "dba","")
			self.con1.close
		except Exception,e:
			pass
		else:
			fail("connection should not be established")


if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(FetchoneTest)
	unittest.TextTestRunner(verbosity=2).run(suite)
