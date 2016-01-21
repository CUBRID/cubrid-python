import unittest
import CUBRIDdb
import locale   
import time     
from xml.dom import minidom

class ExecuteManyTest(unittest.TestCase):
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
                nsql='drop table if exists executemany_tb'
                self.cursor.execute(nsql)
                nsql2='create table executemany_tb(name VARCHAR(40),category VARCHAR(40))'
                self.cursor.execute(nsql2)
        
        def tearDown(self):
                self.cursor.close()
                self.conn.close()

        def test_insert(self):
                print "executemany insert !"
                self.cursor.executemany("insert into executemany_tb values(?,?)",(('name1','category1'),('name2','category2')))
                
                nsql4 = "select count(*) from executemany_tb"
                self.cursor.execute(nsql4)
                self.row_sl=self.cursor.fetchone ()
                c_sl=self.row_sl[0]
                self.assertEqual(c_sl,2)

        def test_select(self):
                print "executemany select !"
                insertSql="INSERT INTO executemany_tb (name, category) VALUES('snake', 'reptile'),('frog', 'amphibian'),('frog2', 'fish'),('racoon', 'mammal') "
                resultInsert=self.cursor.execute(insertSql)
                self.assertEquals(resultInsert,4)
        
                self.cursor.executemany("select * from executemany_tb where name like ?",(('sn%'),('fr%'),('rac%')))
                self.row_sl=self.cursor.fetchall ()
                self.conn.commit()
                for self.result in self.row_sl:
                    print "%s, %s" % (self.result[0], self.result[1])

        def test_update(self):
                print "executemany update!"
                insertSql="INSERT INTO executemany_tb (name, category) VALUES('snake', 'reptile'),('frog', 'amphibian'),('tuna', 'fish'),('racoon', 'mammal') "
                resultInsert=self.cursor.execute(insertSql)
                self.assertEquals(resultInsert,4)


                self.cursor.executemany(" UPDATE executemany_tb SET category =? WHERE name =? ", (('update1', 'snake'),('update2','frog')))
                self.cursor.execute("SELECT name, category FROM executemany_tb")
                self.row_sl=self.cursor.fetchall ()
                self.conn.commit()
                for self.result in self.row_sl:
                    print "%s, %s" % (self.result[0], self.result[1])

        def test_delete(self):
                print "executemany delete!"
                insertSql="INSERT INTO executemany_tb (name, category) VALUES('snake', 'reptile'),('frog', 'amphibian'),('tuna', 'fish'),('racoon', 'mammal') ,('name1','category1'),('name2','category2')"
                resultInsert=self.cursor.execute(insertSql)
                self.assertEquals(resultInsert,6)

                self.cursor.executemany("delete from executemany_tb where name like ?",(('sna%'),('fro%')))

                nsql4 = "select * from executemany_tb"
                self.cursor.execute(nsql4)
                self.row_up=self.cursor.fetchone ()
                print (self.row_up[0],self.row_up[1])
                c_sl=self.row_up[0]
                self.assertEqual(c_sl,'tuna')
                self.row_up=self.cursor.fetchone ()
                print (self.row_up[0],self.row_up[1])
                self.row_up=self.cursor.fetchone ()
                print (self.row_up[0],self.row_up[1])



if __name__ == '__main__':
        suite = unittest.TestLoader().loadTestsFromTestCase(ExecuteManyTest)
        unittest.TextTestRunner(verbosity=2).run(suite)
