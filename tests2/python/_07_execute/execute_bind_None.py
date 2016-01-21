import unittest
import CUBRIDdb
import time

class DBAPI20Test(unittest.TestCase):
    driver = CUBRIDdb
    connect_args = ('CUBRID:localhost:33000:demodb:::', 'dba')
    connect_kw_args = {}

    def setup(self):
        pass

    def tearDown(self):
        pass

    def _connect(self):
        try:
            con = self.driver.connect(
                    *self.connect_args, **self.connect_kw_args
                    )
            return con
        except AttributeError:
            self.fail("No connect method found in self.driver module")

    def test_bind_None(self):
        con = self._connect();
        try:
            c = con.cursor()

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
            con.close()

def suite():
    suite = unittest.TestSuite()
    suite.addTest(DBAPI20Test("test_connect"))
    return suite

if __name__ == '__main__':
    #unittest.main(defaultTest = 'suite')
    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(DBAPI20Test)
    unittest.TextTestRunner(verbosity=2).run(suite)
