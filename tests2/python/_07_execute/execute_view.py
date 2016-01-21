import unittest
import CUBRIDdb
import locale   
import time     
from xml.dom import minidom

class ExecuteViewTest(unittest.TestCase):
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
                #view_tb and view v 
                nsql2='drop table if exists view_tb'
                self.cursor.execute(nsql2)
                nsql3='create table view_tb(qty INT, price INT)'
                self.cursor.execute(nsql3)
                viewSql="INSERT INTO view_tb VALUES (3,50)"
                valueInsert=self.cursor.execute(viewSql)
                self.assertEquals(valueInsert,1)

                print "create view !"
                viewSql2='CREATE VIEW v AS SELECT qty, price, qty*price AS "value" FROM view_tb'
                self.cursor.execute(viewSql2)

                #table a_tbl and view b_view
                nsql2='drop table if exists a_tbl'
                self.cursor.execute(nsql2)
                nsql3='CREATE TABLE a_tbl(id INT NOT NULL,phone VARCHAR(10))'
                self.cursor.execute(nsql3)
                insertSql="INSERT INTO a_tbl VALUES(1,'111-1111'), (2,'222-2222'), (3, '333-3333'), (4, NULL), (5, NULL)"
                valueInsert=self.cursor.execute(insertSql)
                self.assertEquals(valueInsert,5)
                viewSql2='CREATE VIEW b_view AS SELECT * FROM a_tbl WHERE phone IS NOT NULL WITH CHECK OPTION'
                self.cursor.execute(viewSql2)

        def tearDown(self):
                nsql2='drop view v'
                self.cursor.execute(nsql2)

                nsql2='drop view b_view'
                self.cursor.execute(nsql2)
                self.cursor.close()
                self.conn.close()

        def test_select(self):
                print "view: select * from v !"
                self.cursor.execute("select * from v")
                self.row_sl=self.cursor.fetchone()
                print (self.row_sl[0],self.row_sl[1],self.row_sl[2])
                c_sl=self.row_sl[2]
                self.assertEqual(c_sl,150)

                print "view: SHOW CREATE VIEW v !"
                self.cursor.execute("SHOW CREATE VIEW v")
                self.row_sl=self.cursor.fetchone()
                print (self.row_sl[0],self.row_sl[1])
                c_sl=self.row_sl[1]
                self.assertEqual(c_sl,'select [view_tb].[qty], [view_tb].[price], [view_tb].[qty]*[view_tb].[price] from [view_tb] [view_tb]')

        
        def test_alter(self):
                print "view alter!"

                alterSql="ALTER VIEW b_view ADD QUERY SELECT * FROM a_tbl WHERE id IN (1,2)"
                result_up=self.cursor.execute(alterSql)
                print ("alterSql",result_up)
                #self.assertEqual(result_up, 1)
                select_up = "select * from b_view"
                self.cursor.execute(select_up)
                self.row_up=self.cursor.fetchall()
                for self.value in self.row_up:
                   print (self.value[0],self.value[1])
                #result_up1=self.row_up[1]
                #self.assertEqual(result_up1, 'b2')

        def test_update(self):
                print "view update!"

                alterSql="UPDATE b_view SET phone=NULL"
                try:
                   result_up=self.cursor.execute(alterSql)
                   print ("alterSql",result_up)
                except Exception,e:
                   print ("str(e)",e)
                   value=str(e)
                   self.assertEqual(value,"(-495, 'ERROR: DBMS, -495, Execute: Check option exception on view b_view. update a_tbl b_view set b_view.phone=null where ((b_view.phone is not null ))\\n-- check condition: ((b_view.phone is not null ))')")
                

if __name__ == '__main__':
        suite = unittest.TestLoader().loadTestsFromTestCase(ExecuteViewTest)
        unittest.TextTestRunner(verbosity=2).run(suite)
         
