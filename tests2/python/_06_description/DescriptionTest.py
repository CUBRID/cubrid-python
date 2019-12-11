import unittest
import CUBRIDdb
import locale
import time
from xml.dom import minidom

class FetchoneDescriptionTest(unittest.TestCase):
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

		sqlCreate = "create table numeric_db(c_int int, c_short short,c_numeric numeric,c_float float,c_double double,c_monetary monetary)"
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

        def test_desc_num(self):
#               test description of int type
                sqlSelect = "select * from numeric_db"
                self.cur.execute(sqlSelect)
                dataDesc = self.cur.description		
		dataCheck = (('c_int', 8, 0, 0, 10, 0, 1), ('c_short', 9, 0, 0, 5, 0, 1), ('c_numeric', 7, 0, 0, 15, 0, 1), ('c_float', 11, 0, 0, 7, 0, 1), ('c_double', 12, 0, 0, 15, 0, 1), ('c_monetary', 10, 0, 0, 15, 0, 1))
		self.assertEquals(dataCheck, dataDesc)

        def test_desc_datetime(self):
#               test description of datetime type
                sqlSelect = "select * from datetime_db"
                self.cur.execute(sqlSelect)
                dataDesc = self.cur.description
                dataCheck = (('c_date', 13, 0, 0, 10, 0, 1), ('c_time', 14, 0, 0, 8, 0, 1), ('c_datetime', 22, 0, 0, 23, 3, 1), ('c_timestamp', 15, 0, 0, 19, 0, 1))
		self.assertEquals(dataCheck, dataDesc)

        def test_desc_bit(self):
#               test description of bit type
                sqlSelect = "select * from bit_db"
                self.cur.execute(sqlSelect)
                dataDesc = self.cur.description
                dataCheck = (('c_bit', 5, 0, 0, 8, 0, 1), ('c_varbit', 6, 0, 0, 8, 0, 1))
                self.assertEquals(dataCheck, dataDesc)

        def test_desc_char(self):
#               test description of char type
                sqlSelect = "select * from character_db"
                self.cur.execute(sqlSelect)
                dataDesc = self.cur.description
                dataCheck = (('c_char', 1, 0, 0, 4, 0, 1), ('c_varchar', 2, 0, 0, 4, 0, 1), ('c_string', 2, 0, 0, 1073741823, 0, 1), ('c_nchar', 3, 0, 0, 4, 0, 1), ('c_varnchar', 4, 0, 0, 4, 0, 1))
                self.assertEquals(dataCheck, dataDesc)

        def test_desc_collection(self):
#               test description of collection type
                sqlSelect = "select * from collection_db"
                self.cur.execute(sqlSelect)
                dataDesc = self.cur.description
                dataCheck = (('c_set', 32, 0, 0, 0, 0, 1), ('c_multiset', 64, 0, 0, 0, 0, 1), ('c_sequence', 96, 0, 0, 0, 0, 1))
                self.assertEquals(dataCheck, dataDesc)

	def test_all(self):
		sqlSelect = "select * from numeric_db"
                self.cur.execute(sqlSelect)
		print self.cur.description
		sqlSelect = "select * from datetime_db"
                self.cur.execute(sqlSelect)
		print self.cur.description
                sqlSelect = "select * from bit_db"
                self.cur.execute(sqlSelect)
                print self.cur.description
                sqlSelect = "select * from character_db"
                self.cur.execute(sqlSelect)
                print self.cur.description
                sqlSelect = "select * from collection_db"
                self.cur.execute(sqlSelect)
                print self.cur.description		


if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(FetchoneDescriptionTest)
	unittest.TextTestRunner(verbosity=2).run(suite)
