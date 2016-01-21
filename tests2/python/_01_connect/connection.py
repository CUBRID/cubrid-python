import CUBRIDdb
import unittest
import os
import sys
from xml.dom import minidom

class CUBRIDPythonDBITest(unittest.TestCase):

	def setup(self):
		pass
	def tearDown(self):
		pass
	def test_connect(self):
		print("01. Common connection")
                xmlt = minidom.parse('configuration/python_config.xml')
                ips = xmlt.childNodes[0].getElementsByTagName('ip')
                ip = ips[0].childNodes[0].toxml()
                ports = xmlt.childNodes[0].getElementsByTagName('port')
                port = ports[0].childNodes[0].toxml()
                dbnames = xmlt.childNodes[0].getElementsByTagName('dbname')
                dbname = dbnames[0].childNodes[0].toxml()
                conStr = "CUBRID:"+ip+":"+port+":"+dbname+":::"
		self.con=CUBRIDdb.connect(conStr,'dba','')
	        self.c=self.con.cursor()
		self.c.execute("select * from db_class limit 5;")
		row=self.c.fetchone()
		print(row)
		self.c.close()
		self.con.close()
	def test_connect_withautocommit(self):
		print("\n02. Connection with autocommit property")
                xmlt = minidom.parse('configuration/python_config.xml')
                ips = xmlt.childNodes[0].getElementsByTagName('ip')
                ip = ips[0].childNodes[0].toxml()
                ports = xmlt.childNodes[0].getElementsByTagName('port')
                port = ports[0].childNodes[0].toxml()
                dbnames = xmlt.childNodes[0].getElementsByTagName('dbname')
                dbname = dbnames[0].childNodes[0].toxml()
                conStr = "CUBRID:"+ip+":"+port+":"+dbname+":::"
                self.con=CUBRIDdb.connect(conStr)
		#self.con=CUBRIDdb.connect("CUBRID:localhost:33188:pydb:::")
	        self.c=self.con.cursor()
		self.c.execute("select * from db_class limit 5;")
		row=self.c.fetchone()
		print(row)
		self.c.close()
		self.con.close()
	def test_connection_with_wrong_parameter(self):
		print("\n03. Connection with wrong parameter")
		try:
			self.con = CUBRIDdb.connect("CUBRID:10.34.64:300a12:pydb:::?autocommit=false")
		except Exception,e:
                        print("connect error: ", e)
                        #self.con.close()
	def test_connection_with_ip(self):
		print("\n04. Connection with other computer")
                xmlt = minidom.parse('configuration/python_config.xml')
                ips = xmlt.childNodes[0].getElementsByTagName('ip')
                ip = ips[0].childNodes[0].toxml()
                ports = xmlt.childNodes[0].getElementsByTagName('port')
                port = ports[0].childNodes[0].toxml()
                dbnames = xmlt.childNodes[0].getElementsByTagName('dbname')
                dbname = dbnames[0].childNodes[0].toxml()
                remoteips = xmlt.childNodes[0].getElementsByTagName('remoteIP')
                remoteip= remoteips[0].childNodes[0].toxml()
                #conStr = "CUBRID:"+remoteip+":"+port+":"+dbname+":dba::?autocommit=false"
                conStr = "CUBRID:"+remoteip+":"+port+":"+dbname+":dba::"
                print(conStr)
      		self.con=CUBRIDdb.connect(conStr,"dba","")
		self.c=self.con.cursor()
		self.c.execute("select * from db_class;")
		row=self.c.fetchone()
                print(row)
                self.c.close()
                self.con.close()
			
	def test_connection_with_alhost(self):
		print("\n05. Connection with alhost")
                xmlt = minidom.parse('configuration/python_config.xml')
                ips = xmlt.childNodes[0].getElementsByTagName('ip')
                ip = ips[0].childNodes[0].toxml()
                ports = xmlt.childNodes[0].getElementsByTagName('port')
                port = ports[0].childNodes[0].toxml()
                dbnames = xmlt.childNodes[0].getElementsByTagName('dbname')
                dbname = dbnames[0].childNodes[0].toxml()
                remoteips = xmlt.childNodes[0].getElementsByTagName('remoteIP')
                remoteip= remoteips[0].childNodes[0].toxml()
                #conStr = "CUBRID:"+ip+":"+port+":"+dbname+":dba::?althosts="+remoteip+"&autocommit=false"
                conStr = "CUBRID:"+ip+":"+port+":"+dbname+":dba::?altHosts="+remoteip+":30188"
                print(conStr)
                self.con=CUBRIDdb.connect(conStr,"dba","")
		#self.con=CUBRIDdb.connect("CUBRID:10.34.64.35:30012:pydb:dba::?althosts=10.34.64.59:33011&autocommit=false")
		self.c=self.con.cursor()
		self.c.execute("select * from db_class;")
		row=self.c.fetchone()
                print(row)
                self.c.close()
                self.con.close()

if __name__ == '__main__':
       #unittest.main()
       suite = unittest.TestLoader().loadTestsFromTestCase(CUBRIDPythonDBITest)
       unittest.TextTestRunner(verbosity=2).run(suite)
