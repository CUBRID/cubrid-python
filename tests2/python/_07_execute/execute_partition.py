import unittest
import CUBRIDdb
import locale   
import time     
from xml.dom import minidom

class ExecuteNonormalTest(unittest.TestCase):
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
                nsql='drop table if exists partition_tb'
                self.cursor.execute(nsql)
                nsql2="create table partition_tb(id int not null, test_char char(50),test_varchar varchar(2000), test_bit bit(16),test_varbit bit varying(20),test_nchar nchar(50),test_nvarchar nchar varying(2000),test_string string,test_datetime timestamp, primary key (id, test_char))"
                self.cursor.execute(nsql2)

        def tearDown(self):
                self.cursor.close()
                self.conn.close()

        def test_selectEmptyTable(self):
                print "SelectEmptyTable: "
                self.cursor.execute("select count(*) from partition_tb")
                self.row_dl=self.cursor.fetchone ()
                print self.row_dl[0]
                c_dl=self.row_dl[0]
                self.assertEqual(c_dl,0)

                self.cursor.execute("select max(id) from partition_tb")
                self.row_dl=self.cursor.fetchone ()
                print ("max id: ", self.row_dl[0])
                c_dl2=self.row_dl[0]
                self.assertEqual(c_dl2,None)

        def test_alter(self):
                print "add partition!"
                alterSql="ALTER TABLE partition_tb PARTITION BY LIST (test_char) (PARTITION p0 VALUES IN ('aaa','bbb','ddd'),PARTITION p1 VALUES IN ('fff','ggg','hhh',NULL),PARTITION p2 VALUES IN ('kkk','lll','mmm') )"
                resultAlter=self.cursor.execute(alterSql)
                self.assertEquals(resultAlter,0)
        def test_insert(self):
                print "partition insert!"

                alterSql="ALTER TABLE partition_tb PARTITION BY LIST (test_char) (PARTITION p0 VALUES IN ('aaa','bbb','ddd'),PARTITION p1 VALUES IN ('fff','ggg','hhh',NULL),PARTITION p2 VALUES IN ('kkk','lll','mmm') )"
                resultAlter=self.cursor.execute(alterSql)
                self.assertEquals(resultAlter,0)
 
                insertSql="insert into partition_tb values(1,'aaa','aaa',B'1',B'1011',N'aaa',N'aaa','aaaaaaaaaa','2006-03-01 09:00:00')"
                resultInsert=self.cursor.execute(insertSql)
                self.assertEquals(resultInsert,1)
                insertSql2="insert into partition_tb values(5,'ggg','ggg',B'101',B'1111',N'ggg',N'ggg','gggggggggg','2006-03-01 09:00:00')"
                resultInsert2=self.cursor.execute(insertSql2)
                self.assertEquals(resultInsert2,1)
        def test_select(self):
                print "partition select !"

                alterSql="ALTER TABLE partition_tb PARTITION BY LIST (test_char) (PARTITION p0 VALUES IN ('aaa','bbb','ddd'),PARTITION p1 VALUES IN ('fff','ggg','hhh',NULL),PARTITION p2 VALUES IN ('kkk','lll','mmm') )"
                resultAlter=self.cursor.execute(alterSql)
                self.assertEquals(resultAlter,0)

                insertSql="insert into partition_tb values(1,'aaa','aaa',B'1',B'1011',N'aaa',N'aaa','aaaaaaaaaa','2006-03-01 09:00:00')"
                resultInsert=self.cursor.execute(insertSql)
                self.assertEquals(resultInsert,1)
                insertSql2="insert into partition_tb values(5,'ggg','ggg',B'101',B'1111',N'ggg',N'ggg','gggggggggg','2006-03-01 09:00:00')"
                resultInsert2=self.cursor.execute(insertSql2)
                self.assertEquals(resultInsert2,1)
                insertSql3="insert into partition_tb values(10, 'kkk',null,null,null,null,null,null,'2007-01-01 09:00:00');"
                resultInsert3=self.cursor.execute(insertSql3)
                self.assertEquals(resultInsert3,1)                

                selectSql = "select * from partition_tb__p__p0 order by id;"
                self.cursor.execute(selectSql)
                self.row_sl=self.cursor.fetchone ()
                c_sl=self.row_sl[1]
                self.assertEqual(c_sl,'aaa                                               ')

        def test_delete(self):
                print "partition delete!"

                alterSql="ALTER TABLE partition_tb PARTITION BY LIST (test_char) (PARTITION p0 VALUES IN ('aaa','bbb','ddd'),PARTITION p1 VALUES IN ('fff','ggg','hhh',NULL),PARTITION p2 VALUES IN ('kkk','lll','mmm') )"
                resultAlter=self.cursor.execute(alterSql)
                self.assertEquals(resultAlter,0)

                insertSql="insert into partition_tb values(1,'aaa','aaa',B'1',B'1011',N'aaa',N'aaa','aaaaaaaaaa','2006-03-01 09:00:00')"
                resultInsert=self.cursor.execute(insertSql)
                self.assertEquals(resultInsert,1)
                insertSql2="insert into partition_tb values(5,'ggg','ggg',B'101',B'1111',N'ggg',N'ggg','gggggggggg','2006-03-01 09:00:00')"
                resultInsert2=self.cursor.execute(insertSql2)
                self.assertEquals(resultInsert2,1)
                insertSql3="insert into partition_tb values(10, 'kkk',null,null,null,null,null,null,'2007-01-01 09:00:00');"
                resultInsert3=self.cursor.execute(insertSql3)
                self.assertEquals(resultInsert3,1)

                deleteSql="delete from partition_tb where id = 1"
                result_dl=self.cursor.execute(deleteSql)
                self.assertEqual(result_dl, 1)
                select_dl = "select count(*) from partition_tb where id >= 0"
                self.cursor.execute(select_dl)
                self.row_dl=self.cursor.fetchone ()
                c_dl=self.row_dl[0]
                self.assertEqual(c_dl,2)

if __name__ == '__main__':
        suite = unittest.TestLoader().loadTestsFromTestCase(ExecuteNonormalTest)
        unittest.TextTestRunner(verbosity=2).run(suite)
