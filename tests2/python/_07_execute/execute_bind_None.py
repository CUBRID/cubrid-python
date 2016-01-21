import unittest
import CUBRIDdb
import locale
import time
import datetime 
from datetime import time
from datetime import date
from datetime import datetime
from xml.dom import minidom

class DBAPI20Test(unittest.TestCase):
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

    def setup(self):
        pass
        
    def tearDown(self):
		pass

    def test_bind_None(self):
        try:
            conStr = self.getConStr()                
            self.con = CUBRIDdb.connect(conStr, "dba","")
            self.cur = self.con.cursor()
            c = self.cur
            c.execute("DROP TABLE IF EXISTS tst")
            c.execute("CREATE TABLE tst(id integer auto_increment);")
            #args = (1,)
            #c.execute('insert into tst (id) values (?)', args)
            
            #c.execute('select * from tst')
            #rows = c.fetchall()
            
            args = (None,)
            c.execute('insert into tst (id) values (?)', args)
            
            c.execute('select * from tst')
            rows = c.fetchall()
            
            for r in rows:
                print "---", r

            self.assertEqual(len(rows), 1)
            self.assertEqual(len(rows[0]), 1)
            self.assertEqual(rows[0][0], 1)
        finally:
            self.cur.close
            self.con.close

if __name__ == '__main__':
    #unittest.main(defaultTest = 'suite')
    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(DBAPI20Test)
    unittest.TextTestRunner(verbosity=2).run(suite)
