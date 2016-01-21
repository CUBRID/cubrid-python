from xml.dom import minidom
import CUBRIDdb
import _cubrid
from _cubrid import *
import unittest

# APIS-368
class ExceptionsTest(unittest.TestCase):
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
                self.cur.execute("DROP TABLE IF EXISTS exceptions_t")
                self.cur.execute("CREATE TABLE exceptions_t(nameid int primary key ,age int,name VARCHAR(40))")
                self.cur.execute("INSERT INTO exceptions_t (name,nameid,age) VALUES('Mike',1,30),('John',2,28),('Bill',3,45)")
        def tearDown(self):
                self.cur.close
                self.con.close
                
      
        def test_01Exceptions(self):
            con =  self.con
            error = 0
            errorValue = ''
            try:
                cur = con.cursor()
                cur.execute("insert into exceptions_t values error_sql('Hello') ")
            except CUBRIDdb.DatabaseError, e:
                error = 1
                errorValue = str(e)
            finally:
                con.close()
            #print >>sys.stderr,  "\nException...Error %d: %s" % (e.args[0], e.args[1])
            self.assertEqual(error, 1, "catch one except.")
            #print "\n", e.args[0]
            #print "\n", errorValue
            self.assertEquals(errorValue[1:5],"-493")
             
            error = 0
            errorValue = ''
            try:
                cur = con.cursor()
                cur.fetchone()
                cur.execute("insert into exceptions_t values ('forrollback',6,66, 10) ")
            except CUBRIDdb.Error, e:
                error = 1
                errorValue = str(e)
                #print >>sys.stderr,  "\nException...Error %d: %s" % (e.args[0], e.args[1])
            except Exception,e1:
                print "\n",str(e1)
            self.assertEqual(error, 1, "catch one except. OK.")
            self.assertEquals(errorValue, "(-20002, 'ERROR: CCI, -20002, Invalid connection handle')")
            
        
        def test_02Exceptions(self):
                #print "\nconnect url is empty"
                try:
                    self.con = CUBRIDdb.connect("")
                except CUBRIDdb.InterfaceError ,e:
                    errorValue=str(e)
                    #print errorValue
                    self.assertEquals(errorValue,"(-20030, 'ERROR: CCI, -20030, Invalid url string')")

                try:
                    self.con = CUBRIDdb.connect()
                except Exception ,e:
                    errorValue=str(e)
                    #print errorValue
                    self.assertEquals(errorValue,"Required argument 'url' (pos 1) not found")
        def test_03Except_Autocommit(self):
            try:
                self.con.set_autocommit()
            except Exception ,e:
                self.assertEquals(str(e),'''set_autocommit() takes exactly 2 arguments (1 given)''')
            try:
                self.con.set_autocommit('invalid')
            except Exception ,e:
                self.assertEquals(str(e),"Parameter should be a boolean value")

        def test_04Except_isolation(self):
            con = _cubrid.connect("CUBRID:localhost:33000:demodb:::", "public")
            try:
                con.set_isolation_level()
            except Exception ,e:
                self.assertEquals(str(e),'''function takes exactly 1 argument (0 given)''')
            try:
                con.set_isolation_level(-1)
            except Exception ,e:
                self.assertEquals(str(e)[1:5],'-110')
            con.close()
        def test_05Except_schema(self):
            con = _cubrid.connect("CUBRID:localhost:33000:demodb:::", "public")
            try:
                con.schema_info()
            except Exception ,e:
                self.assertEquals(str(e),'''function takes at least 2 arguments (0 given)''')

            try:
                con.schema_info(_cubrid.CUBRID_SCH_ATTRIBUTE, 'test_cubrid')
            except Exception ,e:
                self.assertEquals(str(e)[1:5],'-110')

            try:
                con.schema_info(-100, 'test_cubrid')
            except Exception ,e:
                self.assertEquals(str(e)[1:5],'-300')

            try:
                con.schema_info(_cubrid.CUBRID_SCH_TRIGGER, 'test_cubrid')
            except Exception ,e:
                self.assertEquals(str(e)[1:5],'-300')

            con.close()

        def test_06Except_fetch(self):
            con = _cubrid.connect("CUBRID:localhost:33000:demodb:::", "public")
            cur = con.cursor()
            cur.prepare('select * from test_cubrid')
            cur.execute()
            try:
                row = cur.fetch_row(1,2,3)
            except Exception ,e:
                self.assertEquals(str(e),'''function takes at most 1 argument (3 given)''')
            try:
                row = cur.fetch_row(2)
            except Exception ,e:
                self.assertEquals(str(e)[1:7],'-493')

            try:
                cur.prepare('invalid')
            except Exception ,e:
                self.assertEquals(str(e)[1:7],'-30006')

            con.close()

        def test_07Except_Object(self):
            con = _cubrid.connect("CUBRID:localhost:33000:demodb:::", "public")
            con.close()
            try:
                lob = con.lob()
            except Exception ,e:
                self.assertEquals(str(e)[1:7],'-20018')
            try:
                set = con.set()
            except Exception ,e:
                self.assertEquals(str(e)[1:7],'-20018')

        def test_08Except_Ping(self):
            con = _cubrid.connect("CUBRID:localhost:33000:demodb:::", "public")
            con.close()
            try:
                set = con.ping()
            except Exception ,e:
                self.assertEquals(str(e)[1:7],'-20002')

            try:
                set = con.insert_id()
            except Exception ,e:
                self.assertEquals(str(e)[1:7],'-20002')

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ExceptionsTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
