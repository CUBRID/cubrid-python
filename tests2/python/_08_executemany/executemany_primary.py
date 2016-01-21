import unittest
import CUBRIDdb
import locale   
import time     
from xml.dom import minidom

class ExecuteManyPrimaryTest(unittest.TestCase):
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
               
        def test_insert_select(self):
                print "primary table insert!" 
                self.cursor.executemany("insert into primary_tb values(?,?,?)",(('001','aaaa', 'aaaa'), ('002','bbbb', 'bbbb'),('003','cccc', 'cccc'),('004','dddd', 'dddd'),('005','eeee', 'eeee')))
                nsql4 = "select count(*) from primary_tb"
                self.cursor.execute(nsql4)
                self.row_sl=self.cursor.fetchone ()
                print("count primary_tb",self.row_sl[0])
                self.assertEqual(self.row_sl[0],5)

                print "foreign table insert!"
                self.cursor.executemany("insert into foreign_tb values(?,?,?,?)",( ( '001' , 1,1,'1212'),( '001' , 2,2,'2323'),( '002' , 3,3,'3434'),( '002' , 4,4,'4545'), ( '003' , 5,5,'5656'), ( '003' , 6,6,'6767')))
                nsql4 = "select count(*) from foreign_tb"
                self.cursor.execute(nsql4)
                self.row_sl=self.cursor.fetchone ()
                print("count foreign_tb",self.row_sl[0])
                self.assertEqual(self.row_sl[0],6)       


        def test_update(self):
                print "primary table update!"
                self.cursor.executemany("insert into primary_tb values(?,?,?)",(('001','aaaa', 'aaaa'), ('002','bbbb', 'bbbb'),('003','cccc', 'cccc'),('004','dddd', 'dddd'),('005','eeee', 'eeee')))
                self.cursor.executemany("insert into foreign_tb values(?,?,?,?)",( ( '001' , 1,1,'1212'),( '001' , 2,2,'2323'),( '002' , 3,3,'3434'),( '002' , 4,4,'4545'), ( '003' , 5,5,'5656'), ( '003' , 6,6,'6767')))

                print "primary table update!"
                self.cursor.executemany("update primary_tb set title=? where id like ?",( ('change1','001%'),( 'change2','002%')))
                self.cursor.execute( "select * from primary_tb where title like 'change%'")
                self.row_sl=self.cursor.fetchall()
                for self.value in self.row_sl:
                   print(self.value[0],self.value[1],self.value[2])
                self.cursor.execute( "select count(*) from primary_tb where title like 'change%'")
                self.row_sl=self.cursor.fetchone ()
                print("count primary_tb",self.row_sl[0])
                self.assertEqual(self.row_sl[0],2)

                print "foreign table update!"
                self.cursor.executemany("update foreign_tb set song=? where album like ?",( ('song1','001%'),( 'song2','002%')))
                self.cursor.execute( "select * from foreign_tb where song like 'song%'")
                self.row_sl=self.cursor.fetchall()
                for self.value in self.row_sl:
                   print(self.value[0],self.value[1],self.value[2],self.value[3])
                self.cursor.execute( "select count(*) from foreign_tb where song like 'song%'")
                self.row_sl=self.cursor.fetchone ()
                print("count primary_tb",self.row_sl[0])
                self.assertEqual(self.row_sl[0],4)

        def test_delete(self):
                print "primary table delete!"
                self.cursor.executemany("insert into primary_tb values(?,?,?)",(('001','aaaa', 'aaaa'), ('002','bbbb', 'bbbb'),('003','cccc', 'cccc'),('004','dddd', 'dddd'),('005','eeee', 'eeee')))
                self.cursor.executemany("insert into foreign_tb values(?,?,?,?)",( ( '001' , 1,1,'1212'),( '001' , 2,2,'2323'),( '002' , 3,3,'3434'),( '002' , 4,4,'4545'), ( '003' , 5,5,'5656'), ( '003' , 6,6,'6767')))

                print "primary table delete!"
                try:
                   self.cursor.executemany("delete from primary_tb where id like ?",(('001%'),('002%'),('003%')))
                except Exception,e:
                   value=str(e)
                   print value
                self.assertEqual(value,'(-924, "ERROR: DBMS, -924, Update/Delete operations are restricted by the foreign key \'fk_foreign_tb_album\'.")')
                self.cursor.execute( "select * from primary_tb ")
                self.row_sl=self.cursor.fetchall()
                for self.value in self.row_sl:
                   print(self.value[0],self.value[1],self.value[2])
                self.cursor.execute( "select count(*) from primary_tb ")
                self.row_sl=self.cursor.fetchone ()
                print("count primary_tb",self.row_sl[0])
                self.assertEqual(self.row_sl[0],5)

                print "foreign table delete!"
                self.cursor.executemany("delete from foreign_tb where album like  ?",( ('001%'),('002%')))
                self.cursor.execute( "select * from foreign_tb ")
                self.row_sl=self.cursor.fetchall()
                for self.value in self.row_sl:
                   print(self.value[0],self.value[1],self.value[2],self.value[3])
                self.cursor.execute( "select count(*) from foreign_tb ")
                self.row_sl=self.cursor.fetchone ()
                print("count foreign_tb",self.row_sl[0])
                self.assertEqual(self.row_sl[0],2)



if __name__ == '__main__':
        suite = unittest.TestLoader().loadTestsFromTestCase(ExecuteManyPrimaryTest)
        unittest.TextTestRunner(verbosity=2).run(suite)
         
