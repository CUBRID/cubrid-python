import unittest
import CUBRIDdb
import locale   
import time
import sys     
from xml.dom import minidom

class ExecuteNormalTest(unittest.TestCase):
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
                nsql='drop table if exists tdb'
                self.cursor.execute(nsql)
                nsql2='create table tdb(a int primary key, b varchar(20), c timestamp)'
                self.cursor.execute(nsql2)
                
        def tearDown(self):
                self.cursor.close()
                self.conn.close()
                
        def test_selectVersion(self):
                print "normal select version" 
                self.cursor.execute("SELECT VERSION()")
                self.row=self.cursor.fetchone ()
                c=self.row[0]
                #self.assertEquals(c,'8.4.1.0559')
                
        def test_insert(self):
                print "normal insert!" 
                nsql3="insert into tdb(a,b,c) values (1,'foo_data', systimestamp)"
                c3=self.cursor.execute(nsql3)
                self.assertEquals(c3,1)
                
        def test_select(self):
                print "normal select !"
                for n in range(100):
                   nsql_in = "insert into tdb(a,b,c) values (" + str(n) + " ,'foo_data', systimestamp)"
                   c_in=self.cursor.execute(nsql_in)
                   #self.conn.commit()
                   self.assertEquals(c_in,1)
                
                nsql4 = "select count(*) from tdb where a >= 0"
                self.cursor.execute(nsql4)
                self.row_sl=self.cursor.fetchone ()
                c_sl=self.row_sl[0]
                self.assertEqual(c_sl,100)
                #self.conn.commit()
                
        def test_update(self):
                print "normal update!"
                nsql3="insert into tdb(a,b,c) values (1,'foo_data', systimestamp)"
                c3=self.cursor.execute(nsql3)
                self.assertEquals(c3,1)

                updateSql="update tdb set b = 'foo_data_new' where a = 1"
                result_up=self.cursor.execute(updateSql)
                self.assertEqual(result_up, 1)
                select_up = "select * from tdb where a =1"
                self.cursor.execute(select_up)
                self.row_up=self.cursor.fetchone()
                result_up2=self.row_up[1]
                self.assertEqual(result_up2, 'foo_data_new')
                
        def test_delete(self):
                print "normal delete!"
                nsql3="insert into tdb(a) values (1),(2),(3),(4),(5)"
                c3=self.cursor.execute(nsql3)
                self.assertEquals(c3,5)
                #self.conn.commit()


                deleteSql="delete from tdb where a = 1"
                result_dl=self.cursor.execute(deleteSql)
                self.assertEqual(result_dl, 1)
                select_dl = "select count(*) from tdb where a >= 0"
                self.cursor.execute(select_dl)
                self.row_dl=self.cursor.fetchone ()
                c_dl=self.row_dl[0]
                self.assertEqual(c_dl,4)
                #self.conn.commit()
                

if __name__ == '__main__':
        #suite = unittest.TestLoader().loadTestsFromTestCase(ExecuteNormalTest)
        #unittest.TextTestRunner(verbosity=2).run(suite)
        suite = unittest.TestSuite()
        if len(sys.argv) == 1:
            suite = unittest.TestLoader().loadTestsFromTestCase(ExecuteNormalTest)
        else:
            for test_name in sys.argv[1:]:
                suite.addTest(ExecuteNormalTest(test_name))
        unittest.TextTestRunner(verbosity=2).run(suite)
