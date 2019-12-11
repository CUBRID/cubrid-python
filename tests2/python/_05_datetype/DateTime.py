import unittest
import CUBRIDdb
import datetime
import locale
from xml.dom import minidom

class CubridDataTimeTest(unittest.TestCase):
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
                sqlDrop = "drop table if exists t_datetime"
                self.cur.execute(sqlDrop)
                sqlCreate = "create table t_datetime(c_date date, c_time time, c_datetime datetime, c_timestamp timestamp)"
		self.cur.execute(sqlCreate)

        def tearDown(self):
                sqlDrop = "drop table if exists t_datetime"
                self.cur.execute(sqlDrop)
                self.cur.close
                self.con.close

        def test_cubrid_date(self):
#               test cubrid date
		dataTuple=((1,1,1),(9999,12,31),(2012,2,2))
		dataCheck=[datetime.date(1,1,1),datetime.date(9999,12,31),datetime.date(2012,2,2)]
		for i in range(len(dataTuple)):		
			data = CUBRIDdb.Date(dataTuple[i][0],dataTuple[i][1],dataTuple[i][2])
			print "cubrid date: ",data
	                self.assertEquals(dataCheck[i], data)
#		self.cur.execute("insert into t_datetime(c_date) values ('1-1-1')")

        def test_cubrid_date_invalid(self):
#               test cubrid invalid date
                dataTuple=((1,1,0),(0,1,1),(1,0,1),(10000,12,31),(1,1,32),(1,13,1),(2012,02,30))
                for i in range(len(dataTuple)):
                        try:
				data = CUBRIDdb.Date(dataTuple[i][0],dataTuple[i][1],dataTuple[i][2])
                        except Exception,e:
				print str(e)
			else:
				self.assertTrue(False)

        def test_cubrid_date_invalid2(self):
#               test cubrid invalid params
                dataTuple=((1),(1,1),("1","1","1"))
                for i in range(len(dataTuple)):
                        try:
                                data = CUBRIDdb.Date(dataTuple[i][0],dataTuple[i][1],dataTuple[i][2])
                        except Exception,e:
                                print str(e)
                        else:
                                self.assertTrue(False)

        def test_cubrid_time(self):
#               test cubrid time
                dataTuple=((0,0,0),(12,12,12),(23,59,59))
                dataCheck=[datetime.time(0,0,0),datetime.time(12,12,12),datetime.time(23,59,59)]
                for i in range(len(dataTuple)):
                        data = CUBRIDdb.Time(dataTuple[i][0],dataTuple[i][1],dataTuple[i][2])
                        print "cubrid time: ",data
                        self.assertEquals(dataCheck[i], data)

        def test_cubrid_time_invalid(self):
#               test cubrid invalid time
                dataTuple=((0,0,-1),(0,0,60),(0,-1,0),(0,60,0),(-1,0,0),(24,59,59))
                for i in range(len(dataTuple)):
                        try:
                                data = CUBRIDdb.Time(dataTuple[i][0],dataTuple[i][1],dataTuple[i][2])
                        except Exception,e:
                                print str(e)
                        else:
                                self.assertTrue(False)

        def test_cubrid_time_invalid2(self):
#               test cubrid invalid params
                dataTuple=((0),(0,0),("0","0","0"))
                for i in range(len(dataTuple)):
                        try:
                                data = CUBRIDdb.Time(dataTuple[i][0],dataTuple[i][1],dataTuple[i][2])
                        except Exception,e:
                                print str(e)
                        else:
                                self.assertTrue(False)

        def test_cubrid_timestamp(self):
#               test cubrid timestamp
                dataTuple=((1,1,1,0,0,0),(9999,12,31,23,59,59),(2012,2,2,1,1,1))
                dataCheck=[datetime.datetime(1,1,1,0,0,0),datetime.datetime(9999,12,31,23,59,59),datetime.datetime(2012,2,2,1,1,1)]
                for i in range(len(dataTuple)):
                        data = CUBRIDdb.Timestamp(dataTuple[i][0],dataTuple[i][1],dataTuple[i][2],dataTuple[i][3],dataTuple[i][4],dataTuple[i][5])
                        print "cubrid timestamp: ",data
                        self.assertEquals(dataCheck[i], data)

        def test_cubrid_timestamp_invalid(self):
#               test cubrid invalid timestamp
                dataTuple=((1,1,1,0,0,-1),(1,1,1,0,0,60),(1,1,1,0,-1,0),(1,1,1,0,60,0),(1,1,1,-1,0,0),(1,1,1,24,59,59),(2012,2,30,1,1,1),(2012,2,3,24,29,59))
                for i in range(len(dataTuple)):
                        try:
                                data = CUBRIDdb.Timestamp(dataTuple[i][0],dataTuple[i][1],dataTuple[i][2],dataTuple[i][3],dataTuple[i][4],dataTuple[i][5])
                        except Exception,e:
                                print str(e)
                        else:
                                self.assertTrue(False)

        def test_cubrid_timestamp_invalid2(self):
#               test cubrid invalid params
                dataTuple=((1,1,1),(1,1,1,0,0),("1","1","1","0","0","0"))
                for i in range(len(dataTuple)):
                        try:
                                data = CUBRIDdb.Timestamp(dataTuple[i][0],dataTuple[i][1],dataTuple[i][2],dataTuple[i][3],dataTuple[i][4],dataTuple[i][5])
                        except Exception,e:
                                print str(e)
                        else:
                                self.assertTrue(False)

        def test_cubrid_datefromticks(self):
#               test cubrid dateformticks
                dataTuple=(-86401,0.00,5054400.00,)
                dataCheck=[datetime.date(1969,12,31),datetime.date(1970,1,1),datetime.date(1970,2,28)]
                for i in range(len(dataTuple)):
                        data = CUBRIDdb.DateFromTicks(dataTuple[i])
                        print "cubrid date: ",data
                        self.assertEquals(dataCheck[i], data)

        def test_cubrid_datefromticks_invalid(self):
#               test cubrid invalid tick
                dataTuple=("-1")
                for i in range(len(dataTuple)):
                        try:
                                data = CUBRIDdb.DateFromTicks(dataTuple[i])
                        except Exception,e:
                                print str(e)
                        else:
                                self.assertTrue(False)
                                
        def test_cubrid_timefromticks(self):
#               test cubrid timeformticks
                dataTuple=(0.00,57599.00,57600.00,)
                dataCheck=[datetime.time(9,0,0),datetime.time(0,59,59),datetime.time(1,0,0)]
                print '-----------------------------------------------------------------------------'
                for i in range(len(dataTuple)):
                        data = CUBRIDdb.TimeFromTicks(dataTuple[i])
                        print "cubrid time: ",i, data
                        self.assertEquals(dataCheck[i], data)

        def test_cubrid_timefromticks_invalid(self):
#               test cubrid invalid tick
                dataTuple=("-1")
                for i in range(len(dataTuple)):
                        try:
                                data = CUBRIDdb.TimeFromTicks(dataTuple[i])
                        except Exception,e:
                                print str(e)
                        else:
                                self.assertTrue(False)

        def test_cubrid_timestampfromticks(self):
#               test cubrid timeformticks
                dataTuple=(-1.00,0.00,140399.00,54000.00,)
                dataCheck=[datetime.datetime(1970,1,1,8,59,59),datetime.datetime(1970,1,1,9,0,0),datetime.datetime(1970,1,2,23,59,59),datetime.datetime(1970,1,2,0,0,0)]
                for i in range(len(dataTuple)):
                        data = CUBRIDdb.TimestampFromTicks(dataTuple[i])
                        print "cubrid time: ",data
                        self.assertEquals(dataCheck[i], data)

        def test_cubrid_timestampfromticks_invalid(self):
#               test cubrid invalid tick
                dataTuple=("-1")
                for i in range(len(dataTuple)):
                        try:
                                data = CUBRIDdb.TimestampFromTicks(dataTuple[i])
                        except Exception,e:
                                print str(e)
                        else:
                                self.assertTrue(False)

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(CubridDataTimeTest)
	unittest.TextTestRunner(verbosity=2).run(suite)
