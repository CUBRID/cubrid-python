import unittest
import CUBRIDdb
import locale   
import time     
from xml.dom import minidom

class ExecutePrimaryTest(unittest.TestCase):
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
                nsql1='drop table if exists foreign_tb'
                self.cursor.execute(nsql1)
                nsql2='drop table if exists primary_tb'
                self.cursor.execute(nsql2)
                nsql3='create table primary_tb( id CHAR(10) PRIMARY KEY, title VARCHAR(100), artist VARCHAR(100))'
                self.cursor.execute(nsql3)
                nsql4='create table foreign_tb(album CHAR(10),dsk INTEGER,posn INTEGER,song VARCHAR(255),FOREIGN KEY (album) REFERENCES primary_tb(id) ON UPDATE RESTRICT )'
                self.cursor.execute(nsql4)
                
        def tearDown(self):
                self.cursor.close()
                self.conn.close()
               
        def test_insert(self):
                print "primary table insert!" 
                primarySql="insert into primary_tb values ('001','aaaa', 'aaaa'), ('002','bbbb', 'bbbb'),('003','cccc', 'cccc'),('004','dddd', 'dddd'),('005','eeee', 'eeee')"
                valueInsert=self.cursor.execute(primarySql)
                self.assertEquals(valueInsert,5)

                print "foreign table insert!"
                foreignSql="insert into foreign_tb values ( '001' , 1,1,'1212'),( '001' , 2,2,'2323'), ( '002' , 3,3,'3434'),( '002' , 4,4,'4545'), ( '003' , 5,5,'5656'), ( '003' , 6,6,'6767')"
                valueInsert2=self.cursor.execute(foreignSql)
                self.assertEquals(valueInsert2,6)
           
        def test_select(self):
                print "primary table select !"
                primarySql="insert into primary_tb values ('001','aaaa', 'aaaa'), ('002','bbbb', 'bbbb'),('003','cccc', 'cccc'),('004','dddd', 'dddd'),('005','eeee', 'eeee')"
                valueInsert=self.cursor.execute(primarySql)
                self.assertEquals(valueInsert,5)

                foreignSql="insert into foreign_tb values ( '001' , 1,1,'1212'),( '001' , 2,2,'2323'), ( '002' , 3,3,'3434'),( '002' , 4,4,'4545'), ( '003' , 5,5,'5656'), ( '003' , 6,6,'6767')"
                valueInsert2=self.cursor.execute(foreignSql)
                self.assertEquals(valueInsert2,6)
                
                self.cursor.execute("select title from primary_tb where id like ?",('001%'))
                self.row_sl=self.cursor.fetchone()
                c_sl=self.row_sl[0]
                self.assertEqual(c_sl,'aaaa')

                print "foreign table select!"
                nsql4 = "select song from foreign_tb where dsk=?"
                self.cursor.execute("select song from foreign_tb where dsk=?",(6))
                self.row_sl=self.cursor.fetchone()
                c_sl=self.row_sl[0]
                self.assertEqual(c_sl,'6767')


        def test_update(self):
                print "primary table update!"
                primarySql="insert into primary_tb values ('001','aaaa', 'aaaa'), ('002','bbbb', 'bbbb'),('003','cccc', 'cccc'),('004','dddd', 'dddd'),('005','eeee', 'eeee')"
                valueInsert=self.cursor.execute(primarySql)
                self.assertEquals(valueInsert,5)

                foreignSql="insert into foreign_tb values ( '001' , 1,1,'1212'),( '001' , 2,2,'2323'), ( '002' , 3,3,'3434'),( '002' , 4,4,'4545'), ( '003' , 5,5,'5656'), ( '003' , 6,6,'6767')"
                valueInsert2=self.cursor.execute(foreignSql)
                self.assertEquals(valueInsert2,6)

                updateSql="update primary_tb set id = 'changeid11' where id like '004%'"
                result_up=self.cursor.execute(updateSql)
                self.assertEqual(result_up, 1)
                select_up = "select * from primary_tb where id like 'change%'"
                self.cursor.execute(select_up)
                self.row_up=self.cursor.fetchone()
                print (self.row_up[0],self.row_up[1],self.row_up[2])
                result_up1=self.row_up[2]
                self.assertEqual(result_up1, 'dddd')


                print "foreign table update!"
                updateSql2="update foreign_tb set song = 'changesong' where album like '003%'"
                result_up2=self.cursor.execute(updateSql2)
                self.assertEqual(result_up2, 2)
                select_up2 = "select * from foreign_tb  where album like '003%'"
                self.cursor.execute(select_up2)
                self.row_up2=self.cursor.fetchone()
                print (self.row_up2[0],self.row_up2[1],self.row_up2[2],self.row_up2[3])
                result_up3=self.row_up2[1]
                self.assertEqual(result_up3, 5)
                self.row_up2=self.cursor.fetchone()
                print (self.row_up2[0],self.row_up2[1],self.row_up2[2],self.row_up2[3])
                result_up3=self.row_up2[1]
                self.assertEqual(result_up3, 6)


        def test_delete(self):
                print "primary table delete!"
                primarySql="insert into primary_tb values ('001','aaaa', 'aaaa'), ('002','bbbb', 'bbbb'),('003','cccc', 'cccc'),('004','dddd', 'dddd'),('005','eeee', 'eeee')"
                valueInsert=self.cursor.execute(primarySql)
                self.assertEquals(valueInsert,5)

                foreignSql="insert into foreign_tb values ( '001' , 1,1,'1212'),( '001' , 2,2,'2323'), ( '002' , 3,3,'3434'),( '002' , 4,4,'4545'), ( '003' , 5,5,'5656'), ( '003' , 6,6,'6767')"
                valueInsert2=self.cursor.execute(foreignSql)
                self.assertEquals(valueInsert2,6)

                deleteSql="delete from primary_tb  where id like '004%'"
                result_up=self.cursor.execute(deleteSql)
                self.assertEqual(result_up, 1)
                select_up = "select count(*) from primary_tb "
                self.cursor.execute(select_up)
                self.row_up=self.cursor.fetchone()
                print (self.row_up[0])
                result_up1=self.row_up[0]
                self.assertEqual(result_up1, 4)


                print "foreign table update!"
                deleteSql2="delete from foreign_tb where album like '003%'"
                result_up2=self.cursor.execute(deleteSql2)
                self.assertEqual(result_up2, 2)
                select_up2 = "select count(*) from foreign_tb"
                self.cursor.execute(select_up2)
                self.row_up2=self.cursor.fetchone()
                print (self.row_up2[0])
                result_up3=self.row_up2[0]
                self.assertEqual(result_up3, 4)

if __name__ == '__main__':
        suite = unittest.TestLoader().loadTestsFromTestCase(ExecutePrimaryTest)
        unittest.TextTestRunner(verbosity=2).run(suite)
         
