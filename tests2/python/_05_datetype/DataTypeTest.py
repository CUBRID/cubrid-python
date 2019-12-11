import unittest
import CUBRIDdb
import locale
import time
import datetime 
from datetime import time
from datetime import date
from datetime import datetime
from xml.dom import minidom

class FetchoneTypeTest(unittest.TestCase):
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

		sqlDrop = "drop table if exists numeric_db"
		self.cur.execute(sqlDrop)
		sqlDrop = "drop table if exists datetime_db"
		self.cur.execute(sqlDrop)
		sqlDrop = "drop table if exists bit_db"
		self.cur.execute(sqlDrop)
		sqlDrop = "drop table if exists character_db"
		self.cur.execute(sqlDrop)
		sqlDrop = "drop table if exists collection_db"
		self.cur.execute(sqlDrop)

		sqlCreate = "create table numeric_db(c_int int, c_short short,c_numeric numeric(10,4),c_float float,c_double double,c_monetary monetary)"
		self.cur.execute(sqlCreate)
                sqlCreate = "create table datetime_db(c_date date, c_time time, c_datetime datetime, c_timestamp timestamp)"
                self.cur.execute(sqlCreate)
                sqlCreate = "create table bit_db(c_bit bit(8),c_varbit bit varying(8))"
                self.cur.execute(sqlCreate)
                sqlCreate = "create table character_db(c_char char(4),c_varchar varchar(4),c_string string,c_nchar nchar(4),c_varnchar nchar varying(4))"
                self.cur.execute(sqlCreate)
		sqlCreate = "create table collection_db(c_set set,c_multiset multiset, c_sequence sequence)"
                self.cur.execute(sqlCreate)

	def tearDown(self):
                sqlDrop = "drop table if exists numeric_db"
                self.cur.execute(sqlDrop)
                sqlDrop = "drop table if exists datetime_db"
                self.cur.execute(sqlDrop)
                sqlDrop = "drop table if exists bit_db"
                self.cur.execute(sqlDrop)
                sqlDrop = "drop table if exists character_db"
                self.cur.execute(sqlDrop)
                sqlDrop = "drop table if exists collection_db"
		self.cur.execute(sqlDrop)
		self.cur.close
		self.con.close

        def test_int(self):
#               test valid int type
		dataList = [1,0,-1,2147483647,-2147483648]
                sqlInsert = "insert into numeric_db(c_int) values "
		for i in dataList:
			sqlInsert = sqlInsert + "(" + '%d'%i + "),"
		sqlInsert = sqlInsert.rstrip(',')
                rowNum = self.cur.execute(sqlInsert)
                sqlSelect = "select * from numeric_db"
                self.cur.execute(sqlSelect)
		for i in range(rowNum):
	                data = self.cur.fetchone()
			self.assertEquals(dataList[i], data[0])

        def test_short(self):
#               test normal short type
                dataList = [1,0,-1,32767,-32768]
                sqlInsert = "insert into numeric_db(c_short) values "
                for i in dataList:
                        sqlInsert = sqlInsert + "(" + '%d'%i + "),"
                sqlInsert = sqlInsert.rstrip(',')
                rowNum = self.cur.execute(sqlInsert)
                sqlSelect = "select * from numeric_db"
                self.cur.execute(sqlSelect)
                for i in range(rowNum):
                        data = self.cur.fetchone()
                        self.assertEquals(dataList[i], data[1])
	
        def test_numeric(self):
#               test normal numeric type
                dataList = [12345.6789,0.12345678,-0.123456789]
		dataCheck = [12346,0.1235,-0.1235]
                sqlInsert = "insert into numeric_db(c_numeric) values "
                for i in dataList:
                        sqlInsert = sqlInsert + "(" + '%f'%i + "),"
                sqlInsert = sqlInsert.rstrip(',')
                rowNum = self.cur.execute(sqlInsert)
		sqlSelect = "select * from numeric_db"
                self.cur.execute(sqlSelect)
                for i in range(rowNum):
                        data = self.cur.fetchone()
                        print("numric value: ", data[2])
                        #self.assertEquals(dataCheck[i], data[2])
#                       self.assertEquals(dataCheck[i], locale.atoi(data[2]))

        def test_float(self):
#               test normal float type
                dataList = [1.1,0.0,-1.1]
                sqlInsert = "insert into numeric_db(c_float) values "
                for i in dataList:
                        sqlInsert = sqlInsert + "(" + '%s'%i + "),"
                sqlInsert = sqlInsert.rstrip(',')
                rowNum = self.cur.execute(sqlInsert)
                sqlSelect = "select * from numeric_db"
                self.cur.execute(sqlSelect)
                for i in range(rowNum):
                        data = self.cur.fetchone()
                        self.assertEquals(dataList[i], data[3])

        def test_double(self):
#               test normal double type
                dataList = [1.1,0.0,-1.1]
                sqlInsert = "insert into numeric_db(c_double) values "
                for i in dataList:
                        sqlInsert = sqlInsert + "(" + '%s'%i + "),"
                sqlInsert = sqlInsert.rstrip(',')
                rowNum = self.cur.execute(sqlInsert)
                sqlSelect = "select * from numeric_db"
                self.cur.execute(sqlSelect)
                for i in range(rowNum):
                        data = self.cur.fetchone()
                        self.assertEquals(dataList[i], data[4])

        def test_monetary(self):
#               test normal monetary type
                dataList = [1.1,0.0,-1.1]
                sqlInsert = "insert into numeric_db(c_monetary) values "
                for i in dataList:
                        sqlInsert = sqlInsert + "(" + '%s'%i + "),"
                sqlInsert = sqlInsert.rstrip(',')
                rowNum = self.cur.execute(sqlInsert)
                sqlSelect = "select * from numeric_db"
                self.cur.execute(sqlSelect)
                data = self.cur.fetchone()
                print("data: ", data[5])
                self.assertEquals('1.1000000000000001', data[5])

	def test_char(self):
#		test normal string type
		dataList = ['a','abcd','abcdefg']
		dataCheck = ['a   ','abcd','abcd']
                sqlInsert = "insert into character_db(c_char) values "
                for i in dataList:
                        sqlInsert = sqlInsert + "('" + i + "'),"
                sqlInsert = sqlInsert.rstrip(',')
                rowNum = self.cur.execute(sqlInsert)
                sqlSelect = "select * from character_db"
                self.cur.execute(sqlSelect)
                for i in range(rowNum):
                        data = self.cur.fetchone()
                        self.assertEquals(dataCheck[i], data[0])

        def test_varchar(self):
#                print "test normal string type"
                dataList = ['a','abcd','abcdefg']
                dataCheck = ['a','abcd','abcd']
                sqlInsert = "insert into character_db(c_varchar) values "
                for i in dataList:
                        sqlInsert = sqlInsert + "('" + i + "'),"
                sqlInsert = sqlInsert.rstrip(',')
                rowNum = self.cur.execute(sqlInsert)
                sqlSelect = "select * from character_db"
                self.cur.execute(sqlSelect)
                for i in range(rowNum):
                        data = self.cur.fetchone()
                        self.assertEquals(dataCheck[i], data[1])

        def test_string(self):
#                print "test normal string type"
                dataList = ['a','abcd','abcdefg']
                dataCheck = ['a','abcd','abcdefg']
                sqlInsert = "insert into character_db(c_string) values "
                for i in dataList:
                        sqlInsert = sqlInsert + "('" + i + "'),"
                sqlInsert = sqlInsert.rstrip(',')
                rowNum = self.cur.execute(sqlInsert)
                sqlSelect = "select * from character_db"
                self.cur.execute(sqlSelect)
                for i in range(rowNum):
                        data = self.cur.fetchone()
                        self.assertEquals(dataCheck[i], data[2])

        def test_date(self):
#               test normal date type
                dataList = [date.min,date.today(),date.max]
                sqlInsert = "insert into datetime_db(c_date) values "
                for i in dataList:
                        sqlInsert = sqlInsert + "('" + i.isoformat() + "'),"
                sqlInsert = sqlInsert.rstrip(',')
                rowNum = self.cur.execute(sqlInsert)
                sqlSelect = "select * from datetime_db"
                self.cur.execute(sqlSelect)
                for i in range(rowNum):
                        data = self.cur.fetchone()
                        self.assertEquals(dataList[i], data[0])

        def test_time(self):
#               test normal time type
                dataList = [time.min,time.max]
                sqlInsert = "insert into datetime_db(c_time) values "
                for i in dataList:
                        sqlInsert = sqlInsert + "('" + i.isoformat() + "'),"
                sqlInsert = sqlInsert.rstrip(',')
                rowNum = self.cur.execute(sqlInsert)
                sqlSelect = "select * from datetime_db"
                self.cur.execute(sqlSelect)
                for i in range(rowNum):
                        data = self.cur.fetchone()
                        self.assertEquals(dataList[i].isoformat().rstrip('9').rstrip('.'), data[1].isoformat())

        def test_datetime(self):
#               test normal datetime type
                dataList = [datetime.min,datetime.today(),datetime.now(),datetime.max]
                print ("\ndataList: ",dataList)
                sqlInsert = "insert into datetime_db(c_datetime) values "
                for i in dataList:
                        sqlInsert = sqlInsert + "('" + i.isoformat() + "'),"
                sqlInsert = sqlInsert.rstrip(',')
                rowNum = self.cur.execute(sqlInsert)
                sqlSelect = "select * from datetime_db"
                self.cur.execute(sqlSelect)
                #for i in range(rowNum):
                data = self.cur.fetchone()
                #print data[2]
                self.assertEquals('0001-01-01 00:00:00', data[2].isoformat(" "))

        def test_timestamp(self):
#               test normal datetime type
                dataList = ['10/31','10/31/2008','13:15:45 10/31/2008']
		dataCheck = ['2019-10-31 00:00:00','2008-10-31 00:00:00','2008-10-31 13:15:45']
                sqlInsert = "insert into datetime_db(c_timestamp) values "
                for i in dataList:
                        sqlInsert = sqlInsert + "('" + i + "'),"
                sqlInsert = sqlInsert.rstrip(',')
                rowNum = self.cur.execute(sqlInsert)
                sqlSelect = "select c_timestamp from datetime_db"
                self.cur.execute(sqlSelect)
                for i in range(rowNum):
                        data = self.cur.fetchone()
                        self.assertEquals(dataCheck[i], data[0].isoformat(" "))

        def test_bit(self):
#               test normal bit type
                dataList = ['B\'1\'','B\'1010\'']
                dataCheck = ['80','A0']
                sqlInsert = "insert into bit_db(c_bit) values "
                for i in dataList:
                        sqlInsert = sqlInsert + "(" + i + "),"
                sqlInsert = sqlInsert.rstrip(',')
		rowNum = self.cur.execute(sqlInsert)
                sqlSelect = "select * from bit_db"
                self.cur.execute(sqlSelect)
                for i in range(rowNum):
                        data = self.cur.fetchone()
                        self.assertEquals(dataCheck[i], data[0])


if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(FetchoneTypeTest)
	unittest.TextTestRunner(verbosity=2).run(suite)
