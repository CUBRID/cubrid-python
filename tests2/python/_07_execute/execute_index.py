import unittest
import CUBRIDdb
import locale   
import time     
from xml.dom import minidom

class ExecuteIndexTest(unittest.TestCase):
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
                nsql2='drop class if exists t'
                self.cursor.execute(nsql2)
                nsql2='drop class if exists u'
                self.cursor.execute(nsql2)

                self.cursor.execute("create table t(id int, val int, fk int)")
                self.cursor.execute("create table u(id int, val int,text string)")
                self.cursor.execute("create index _t_id on t(id)")
                self.cursor.execute("create index _t_val on t(val)")
                self.cursor.execute("create index _u_id on u(id)")
                self.cursor.execute("create index _u_val on u(val)")
                self.cursor.execute("create index _u_r_text on u(text)")
                self.cursor.execute("insert into t values (1, 100, 1),(2, 200, 1),(3, 300, 2),(4, 300, 3)")
                self.cursor.execute("insert into u values (1, 1000, '1000 text'),(2, 2000, '2000 text'),(3, 3000, '3000 text'),(3, 3001, '3001 text')")

                
        def tearDown(self):
                self.cursor.close()
                self.conn.close()


        def test_select(self):
                print "single index  select !"
                self.cursor.execute("select * from t use index (_t_id) where id < 2")
                self.row_sl=self.cursor.fetchone()
                print (self.row_sl[0],self.row_sl[1],self.row_sl[2])
                self.assertEqual(self.row_sl[0],1)

                print "select /*+ recompile */"
                self.cursor.execute("select /*+ recompile */ * from t use index (_t_id) where id > 1;")
                self.row_sl=self.cursor.fetchall()
                for self.value in self.row_sl:
                   print (self.value[0],self.value[1],self.value[2])
                self.cursor.execute("select /*+ recompile */ count(*) from t use index (_t_id) where id > 1;")
                self.row_sl=self.cursor.fetchone()
                self.assertEqual(self.row_sl[0],3)

                print "join tests"
                self.cursor.execute("select /*+ recompile */ * from t force index (_t_val) inner join u use index (_u_id) on t.fk = u.id where right(text, 2) < 'zz' and u.id < 100")
                self.row_sl=self.cursor.fetchall()
                for self.value in self.row_sl:
                   print (self.value[0],self.value[1],self.value[2],self.value[3],self.value[4],self.value[5])
                self.cursor.execute("select /*+ recompile */ count(*) from t force index (_t_val) inner join u use index (_u_id) on t.fk = u.id where right(text, 2) < 'zz' and u.id < 100")
                self.row_sl=self.cursor.fetchone()
                self.assertEqual(self.row_sl[0],5)

                print "SUBSELECT tests"
                self.cursor.execute("select /*+ recompile */ * from t force index (_t_val) inner join (select * from u force index (_u_id) where right(text, 2) < 'zz') x on t.fk = x.id ")
                self.row_sl=self.cursor.fetchall()
                for self.value in self.row_sl:
                   print (self.value[0],self.value[1],self.value[2],self.value[3],self.value[4],self.value[5])
                self.cursor.execute("select /*+ recompile */ count(*) from t force index (_t_val) inner join (select * from u force index (_u_id) where right(text, 2) < 'zz') x on t.fk = x.id")
                self.row_sl=self.cursor.fetchone()
                self.assertEqual(self.row_sl[0],5) 

        def test_update(self):
                print "index update!"
                result_up=self.cursor.execute("update t use index (_t_id, _t_val) set val = 1000 where id <4")
                self.assertEqual(result_up, 3)
                select_up = "select * from t"
                self.cursor.execute(select_up)
                self.row_sl=self.cursor.fetchall()
                for self.value in self.row_sl:
                   print (self.value[0],self.value[1],self.value[2])
                self.cursor.execute("select count(*) from t where val=1000")      
                self.row_sl=self.cursor.fetchone()         
                self.assertEqual(self.row_sl[0], 3)

        def test_delete(self):
                print "index  delete!"

                self.cursor.executemany("delete from t use index (_t_id, _t_val) where id =?",((1),(4),(3)))
                self.cursor.execute("select * from t")
                self.row_up=self.cursor.fetchone()
                print (self.row_up[0],self.row_up[1],self.row_up[2])
                result_up1=self.row_up[0]
                self.assertEqual(result_up1, 2)
        
if __name__ == '__main__':
        suite = unittest.TestLoader().loadTestsFromTestCase(ExecuteIndexTest)
        unittest.TextTestRunner(verbosity=2).run(suite)
         
