import unittest
import _cubrid
from _cubrid import *
import time
import sys
import os
import os.path
from xml.dom import minidom

class DatabaseTest(unittest.TestCase):
    driver = _cubrid
    xmlt = minidom.parse('configuration/python_config.xml')
    ips = xmlt.childNodes[0].getElementsByTagName('ip')
    ip = ips[0].childNodes[0].toxml()
    ports = xmlt.childNodes[0].getElementsByTagName('port')
    port = ports[0].childNodes[0].toxml()
    dbnames = xmlt.childNodes[0].getElementsByTagName('dbname')
    dbname = dbnames[0].childNodes[0].toxml()
    conStr = "CUBRID:"+ip+":"+port+":"+dbname+":::"    
    connect_args = (conStr, 'public')
    connect_kw_args = {}

    def setUp(self):
        #con = self._connect()
        #cursor=con.cursor()
        pass

    def tearDown(self):
        #cursor.execute("drop class if exists test_date")
        #con.close()
        #cursor.close()
        pass

    def _connect(self):
        try:
            return self.driver.connect(
                    *self.connect_args, **self.connect_kw_args
                    )
        except AttributeError:
            self.fail("No connect method found in self.driver module")
            
    def test_connect(self):
        con = self._connect()
        con.close()

    def test_server_version(self):
        con = self._connect()
        try:
            print("server version: ", con.server_version()) 
        finally:
            con.close()

    def test_client_version(self):
        con = self._connect()
        try:
            print("client version: ", con.client_version())
        finally:
            con.close()

    def test_Exceptions(self):
        # Make sure required exceptions exist, and are in the
        # defined heirarchy.
        self.failUnless(
                issubclass(self.driver.InterfaceError, self.driver.Error)
                )
        self.failUnless(
                issubclass(self.driver.DatabaseError,self.driver.Error)
                )
        self.failUnless(
                issubclass(self.driver.NotSupportedError,self.driver.Error)
                )


    def test_commit(self):
        con = self._connect()
        try:
            # Commit must work, even if it doesn't do anything
            con.commit()
        finally:
            con.close()

    def test_rollback(self):
        con = self._connect()
        try:
            con.rollback()
        finally:
            con.close()

    def test_cursor(self):
        con = self._connect()
        try:
            cur = con.cursor()
        finally:
            cur.close()
            con.close()

    def test_cursor_isolation(self):
        con = self._connect()
        try:
            # Make sure cursors created from the same connection have
            # the documented transaction isolation level
            cur1 = con.cursor()
            cur2 = con.cursor()
            cur1.prepare("drop table if exists test_cubrid")
            cur1.execute()
            cur1.prepare('create table test_cubrid (name varchar(20))')
            cur1.execute()
            cur1.prepare("insert into test_cubrid values ('Blair')")
            cur1.execute()
            self.assertEqual(cur1.affected_rows(), 1)
            cur2.prepare('select * from test_cubrid')
            cur2.execute()
            self.assertEqual(cur2.num_rows(), 1)
        finally:
            con.close()

    def test_description(self):
        con = self._connect();
        try:
            cur = con.cursor()
            cur.prepare("drop table if exists test_cubrid")
            cur.execute()
            cur.prepare("create table test_cubrid (name varchar(20))")
            cur.execute()
            self.assertEqual(cur.description, None,
                    'cursor.description should be none after executing a '
                    'statement that can return no rows (such as create)')
            cur.prepare("select name from test_cubrid")
            cur.execute()
            self.assertEqual(len(cur.description), 1,
                    'cursor.description describes too many columns')
            self.assertEqual(len(cur.description[0]), 7,
                    self.assertEqual(len(cur.description[0]), 7,))
            self.assertEqual(cur.description[0][0].lower(), 'name',
                    'cursor.description[x][0] must return column name')
            cur.close()
        finally:
            con.close()


    def test_rowcount(self):
        con = self._connect()
        try:
            cur = con.cursor()
            cur.prepare("drop table if exists test_cubrid")
            cur.execute()
            cur.prepare("create table test_cubrid (name varchar(20))")
            cur.execute()
            self.assertEqual(cur.rowcount, -1, 
                    'cursor.rowcount should be -1 after executing '
                    'no-result statements')
            cur.prepare("insert into test_cubrid value ('Blair')")
            cur.execute()
            self.failUnless(cur.rowcount in (-1, 1),
                    'cursor.rowcount should == number or rows inserted, or '
                    'set to -1 after executing an insert statment')
            cur.prepare("select name from test_cubrid")
            cur.execute()
            self.failUnless(cur.rowcount in (-1,1),
                    'cursor.rowcount should == number of rows returned, or '
                    'set to -1 after executing a select statement')
            cur.close()
        finally:
            con.close()

    def test_isolation_level(self):
        con = self._connect()
        try:
            con.set_isolation_level(CUBRID_REP_CLASS_COMMIT_INSTANCE)
            self.assertEqual(con.isolation_level, 'CUBRID_REP_CLASS_COMMIT_INSTANCE',
                    'connection.set_isolation_level does not work')
        finally:
            con.close()
        
    def test_autocommit(self):
        con = self._connect()
        try:
            self.assertEqual(con.autocommit, True,
                    'connection.autocommit default is TRUE')
            con.set_autocommit(True)
            self.assertEqual(con.autocommit, True,
                    'connection.autocommit should TURE after set on')
            con.set_autocommit(False)
            self.assertEqual(con.autocommit, False,
                    'connection.autocommit should FALSE after set on')
        finally:
            con.close()

    def test_ping(self):
        con = self._connect()
        try:
            self.assertEqual(con.ping(), 1,
                    'connection.ping should return 1 when connect')
        finally:
            con.close()

    def test_schema_info(self):
        con = self._connect()
        try:
            schema_info = con.schema_info(CUBRID_SCH_TABLE, "db_class")
            self.assertEqual(schema_info[0], 'db_class',
                    'connection.schema_info get incorrect result')
            self.assertEqual(schema_info[1], 0,
                    'connection.schema_info get incorrect result')
        finally:
            con.close()

    def test_insert_id(self):
        t_insert_id = 'create table test_cubrid (id numeric auto_increment(1000000000000, 2), name varchar)'
        con = self._connect()
        cur = con.cursor()
        try:

            cur.prepare("drop table if exists test_cubrid")
            cur.execute()
            cur.prepare(t_insert_id)
            cur.execute()
            cur.prepare("insert into test_cubrid(name) values ('Blair')")
            cur.execute()
            insert_id = con.insert_id()
            print("insert_id", insert_id)
            cur.prepare('select * from test_cubrid')
            cur.execute()
            row = cur.fetch_row()
            #self.assertEqual(row[0], insert_id,'connection.insert_id() get incorrect result')
        finally:
            cur.close()
            con.close()

    samples = [
        'Carlton Cold',
        'Carlton Draft',
        'Mountain Goat',
        'Redback',
        'Victoria Bitter',
        'XXXX'
        ]

    def _prepare_data(self, cursor):
        cursor.prepare("insert into test_cubrid values (?),(?),(?),(?),(?),(?)")
        for i in range(len(self.samples)):
            cursor.bind_param(i+1, self.samples[i])
        cursor.execute()

    def _select_data(self, cursor):
        cursor.prepare("select * from test_cubrid")
        cursor.execute()

    def test_affected_rows(self):
        t_affected_rows = 'create table test_cubrid (name varchar(20))'
        con = self._connect()
        cur = con.cursor()
        try:

            cur.prepare("drop table if exists test_cubrid")
            cur.execute()
            cur.prepare(t_affected_rows)
            cur.execute()
            self._prepare_data(cur)
            self.failUnless(cur.affected_rows() in (-1, 6))
            self.assertEqual(cur.num_fields(), None,'cursor.num_fields() should be None when not execute select statement')
            self.assertEqual(cur.num_rows(), None,'cursor.num_rows() should be None when not execute select statement')
        finally:
            cur.close()
            con.close()

    def test_data_seek(self):
        t_data_seek = 'create table test_cubrid (name varchar(20))'
        con = self._connect()
        cur = con.cursor()
        try:
            cur.prepare("drop table if exists test_cubrid")
            cur.execute()
            cur.prepare(t_data_seek)
            cur.execute()
            self._prepare_data(cur)
            self._select_data(cur)

            self.assertEqual(cur.num_fields(), 1,
                    'cusor.num_fields() get incorrect result')
            self.assertEqual(cur.num_rows(), cur.rowcount,
                    'cursor.num_rows() get incorrect result')
            cur.data_seek(3)
            self.assertEqual(cur.row_tell(), 3,
                    'cursor.dataseek get incorrect cursor')

            # if input wrong param, there should be an exception
            # cur.data_seek(7)
        finally:
            cur.close()
            con.close()

    def test_row_seek(self):
        t_row_seek = 'create table test_cubrid (name varchar(20))'
        con = self._connect()
        cur = con.cursor()
        try:
            cur.prepare("drop table if exists test_cubrid")
            cur.execute()
            cur.prepare(t_row_seek)
            cur.execute()
            self._prepare_data(cur)
            self._select_data(cur)
            cur.data_seek(3)
            cur.row_seek(-2)
            self.assertEqual(cur.row_tell(), 1,
                    'cursor.row_seek return incorrect cursor')
            cur.row_seek(4)
            self.assertEqual(cur.row_tell(), 5, 
                    'cursor.row_seek move forward error')
        finally:
            cur.close()
            con.close()
   
    def test_bind_int(self):
        t_bind_int = 'create table test_int (id int)'
        samples_int = ['100', '200', '300', '400']
        con = self._connect()
        cur = con.cursor()
        try:
            cur.prepare("drop table if exists test_int")
            cur.execute()
            cur.prepare(t_bind_int);
            cur.execute()
            cur.prepare("insert into test_int values (?),(?),(?),(?)")
            for i in range(len(samples_int)):
                cur.bind_param(i+1, samples_int[i])
            cur.execute()
            self.failUnless(cur.affected_rows() in (-1, 4))
        finally:
            cur.close()
            con.close()

    def test_bind_float(self):
        ddl_float = 'create table test_float (id float)'
        con = self._connect()
        cur = con.cursor()
        try:
            cur.prepare("drop table if exists test_float")
            cur.execute()
            cur.prepare(ddl_float)
            cur.execute()            
            cur.prepare("insert into test_float values (?)")
            cur.bind_param(1, '3.14')
            cur.execute()
            self.failUnless(cur.affected_rows() in (-1, 1))
        finally:
            cur.close()
            con.close()

    def test_bind_date_e(self):
        ddl_date = 'create table test_date (birthday date)'
        con = self._connect()
        cur = con.cursor()
        try:
            cur.prepare("drop table if exists test_date")
            cur.execute()
            cur.prepare(ddl_date)
            cur.execute()
            cur.prepare('insert into test_date values (?)')
            # if pass wrong params, there should be an exception
            cur.bind_param(1, '2011-02-31')
            cur.execute()
        except Exception,e:
            errorValue=str(e)
            print errorValue
            self.assertEqual(errorValue[1:5],"-494")
        finally:
            cur.close()
            con.close()

    def test_bind_date(self):
        ddl_date = 'create table test_date (birthday date)'
        con = self._connect()
        cur = con.cursor()
        try:
            cur.prepare("drop table if exists test_date")
            cur.execute()
            cur.prepare(ddl_date)
            cur.execute()
            cur.prepare('insert into test_date values (?),(?)')
            cur.bind_param(1, '12/25/2008')
            cur.bind_param(2, '2008-12-25')
            cur.execute()
        finally:
            cur.close()
            con.close()

    def test_bind_time(self):
        ddl_date = 'create table test_date (lunch time)'
        con = self._connect()
        cur = con.cursor()
        try:
            cur.prepare("drop table if exists test_date")
            cur.execute()
            cur.prepare(ddl_date)
            cur.execute()
            cur.prepare('insert into test_date values (?),(?)')
            cur.bind_param(1, '13:10:30')
            cur.bind_param(2, '03:10:36')
            cur.execute()
        finally:
            cur.close()
            con.close()

    def test_bind_timestamp(self):
        ddl_date = 'create table test_date (lunch timestamp)'
        con = self._connect()
        cur = con.cursor()
        try:
            cur.prepare("drop table if exists test_date")
            cur.execute()
            cur.prepare(ddl_date)
            cur.execute()
            cur.prepare('insert into test_date values (?),(?)')
            cur.bind_param(1, '12:00:00 AM 10/31/2011' )
            cur.bind_param(2, '01:15:45 PM 10/31/2008')
            cur.execute()
        finally:
            cur.close()
            con.close()

    def test_lob_file(self):
        t_blob = 'create table test_blob (picture blob)'
        con = self._connect()
        cur = con.cursor()
        try:
            cur.prepare("drop table if exists test_blob")
            cur.execute()
            cur.prepare(t_blob)
            cur.execute()
            cur.prepare('insert into test_blob values (?)')
            lob = con.lob()
            lob.imports(os.path.dirname(sys.argv[0])+'/cubrid_logo.png')
            cur.bind_lob(1, lob)
            cur.execute()
            lob.close()

            cur.prepare('select * from test_blob')
            cur.execute()
            lob_fetch = con.lob()
            cur.fetch_lob(1, lob_fetch)
            lob_fetch.export('out')
            lob_fetch.close()
        finally:
            cur.close()
            con.close()

    def test_lob_string(self):
        t_clob = 'create table test_clob (content clob)'
        con = self._connect()
        cur = con.cursor()
        try:
            cur.prepare("drop table if exists test_clob")
            cur.execute()
            cur.prepare(t_clob)
            cur.execute()
            cur.prepare('insert into test_clob values (?)') 
            lob = con.lob()
            lob.write('hello world', 'C')
            cur.bind_lob(1, lob)
            cur.execute()
            lob.close()

            cur.prepare('select * from test_clob')
            cur.execute()
            lob_fetch = con.lob()
            cur.fetch_lob(1, lob_fetch)
            self.assertEqual(lob_fetch.read(), 'hello world',
                    'lob.read() get incorrect result')
            self.assertEqual(lob_fetch.seek(0, SEEK_SET), 0)
            lob_fetch.close()
        finally:
            cur.close()
            con.close()

    def test_result_info(self):
        t_result_info = 'create table test_result_info (id int primary key, name varchar(20))'
        con = self._connect()
        cur = con.cursor()
        try:
            cur.prepare("drop table if exists test_result_info")
            cur.execute()
            cur.prepare(t_result_info)
            cur.execute()
            cur.prepare("insert into test_result_info values (?,?)")
            cur.bind_param(1, '1000')
            cur.prepare('select * from test_result_info')
            cur.execute()
            info = cur.result_info()
            self.assertEqual(len(info), 2,
                    'the length of cursor.result_info is 2')
            self.assertEqual(info[0][10], 1,
                    'the first colnum of cursor.result should be primary key')

            info = cur.result_info(1)
            self.assertEqual(len(info), 1,
                    'the length of cursor.result_info is 1')
            self.assertEqual(info[0][4], 'id',
                    'cursor.result has just one colname and the name is "name"')
        finally:
            cur.close()
            con.close()
    
def suite():
    suite = unittest.TestSuite()
    suite.addTest(DatabaseTest("test_bind_timestamp"))
    return suite

if __name__ == '__main__':
    #unittest.main(defaultTest = 'suite')
    #unittest.main()
    #suite = unittest.TestLoader().loadTestsFromTestCase(DatabaseTest)
    #unittest.TextTestRunner(verbosity=2).run(suite)
    suite = unittest.TestSuite()
    if len(sys.argv) == 1:
        suite = unittest.TestLoader().loadTestsFromTestCase(DatabaseTest)
    else:
        for test_name in sys.argv[1:]:
            suite.addTest(DatabaseTest(test_name))
    unittest.TextTestRunner(verbosity=2).run(suite)
