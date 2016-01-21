import threading
import time
import CUBRIDdb
from time import sleep,ctime
from xml.dom import minidom

class MyThread(threading.Thread):
	def __init__(self, name=''):
		threading.Thread.__init__(self)
		self.name=name
	#	self.start=s
	#	self.end=d

	def run(self):
                conStr = getConStr()
                self.conn = CUBRIDdb.connect(conStr, "dba","")
                self.cur= self.conn.cursor()
		##start db operation using multiple threads
	        start_time=time.time()
   		if self.name=='insert':
			self.insert_test()
		elif self.name=='delete':
			self.delete_test()
		elif self.name=='update':
			self.update_test()
		elif self.name=='select':
			self.select_test()
		else:
			pass
		end_time=time.time()
		elapse_time=end_time-start_time
		print ("**The operation - " + self.name + " ,total elapse time:" + '%f'%elapse_time + " sec.")

		#for i in range(10):
		#	print 'Start run, the name is ',self.name
		#	time.sleep(1)
	def insert_test(self):
		print "start insert..."
                each_st_time=time.time()
		for n in range(10000000):
			sql="insert into tdb values("+ str(n) + ", 'systimestamp +  pefor', systimestamp, "+ str(n) +");"
			self.cur.execute(sql)
		each_ed_time=time.time()
                eslap_time=each_ed_time-each_st_time
                print ("**The operation is insert, and the elapse time for insert:" + '%f'%eslap_time + "sec.")
                print
                

	def delete_test(self):
		print "start delete..."
                each_st_time=time.time()
                for n in range(10000000):
			limit_num=0
			if (n==0) or (n==1):
				limit_num=1
			else:
				limit_num=n*100

                        sql="delete from tdb where a<" + '%d'%limit_num
			print(sql)
                        self.cur.execute(sql)
                each_ed_time=time.time()
                eslap_time=each_ed_time-each_st_time
                print ("**The operation is delete, and the elapse time for one commit:" + '%f'%eslap_time + "sec.")
		print

	def update_test(self):
		print "start update..."
                each_st_time=time.time()
                for n in range(10000000):
                        sql="update tdb set e = e + 10000000 where a=" + '%d'%n
                        self.cur.execute(sql)
                each_ed_time=time.time()
                eslap_time=each_ed_time-each_st_time
                print ("**The operation is update, and the elapse time for one commit:" + '%f'%eslap_time + "sec.")
		print

	def select_test(self):
		print "start select..."
                each_st_time=time.time()
		for n in range(10000000):
			limit_num=0
			if (n==0) or (n==1):
				limit_num=2
			else:
				limit_num=(n+1)*100
	
			sql="select * from tdb where a <" + '%d'%limit_num
			#print(sql)
			self.cur.execute(sql)
		each_ed_time=time.time()
		eslap_time=each_ed_time-each_st_time
                print ("**The operation is select, and the elapse for each time:" + '%f'%eslap_time + "sec.")
	        print

def getConStr():
	xmlt = minidom.parse('configuration/python_config.xml')
	ips = xmlt.childNodes[0].getElementsByTagName('ip')
	ip = ips[0].childNodes[0].toxml()
	ports = xmlt.childNodes[0].getElementsByTagName('port')
	port = ports[0].childNodes[0].toxml()
	dbnames = xmlt.childNodes[0].getElementsByTagName('dbname')
	dbname = dbnames[0].childNodes[0].toxml()
	conStr = "CUBRID:"+ip+":"+port+":"+dbname+":::"
	return conStr

def test_one_thread():
	conStr = getConStr()
	conn = CUBRIDdb.connect(conStr, "dba","")
	cur= conn.cursor()
	cur.execute('drop table if exists tdb')
	cur.execute('create table tdb(a int, b varchar(20), c timestamp, e int)')	
	
	print 'starting one thread operation at:',ctime()
	t1=MyThread('insert')
	t1.start()
	t1.join()
	t1=MyThread('select')
	t1.start()
	t1.join()
	t1=MyThread('update')
	t1.start()
	t1.join()
	t1=MyThread('delete')
	t1.start()
	t1.join()
	time.sleep(1)
	cur.execute('drop table if exists tdb')

def test_ten_thread():
        conStr = getConStr()
        conn = CUBRIDdb.connect(conStr, "dba","")
        cur= conn.cursor()
        cur.execute('drop table if exists tdb')
        cur.execute('create table tdb(a int, b varchar(20), c timestamp, e int)')

	thrs=[]
	print 'starting ten thread for insert operation at:', ctime()
	for i in range(10):
		t=MyThread('insert')
		thrs.append(t)
	for n in range(10):
		thrs[n].start()
	for j in range(10):
		thrs[j].join()
	print 'end insert!'

	print 'starting ten thread for select operation at:', ctime()
	thrs1=[]
	for i in range(10):
		t1=MyThread('select')
		thrs1.append(t1)
	for n in range(10):
		thrs1[n].start()
	for j in range(10):
		thrs1[j].join()
	print 'end select!'
	
	print 'starting ten thread for update operation at:', ctime()
	thrs2=[]
	for i in range(10):
		t2=MyThread('update')
		thrs2.append(t2)
	for n in range(10):
		thrs2[n].start()
	for j in range(10):
		thrs2[j].join()
	print 'end update!'

	print 'starting ten thread for delete operation at:', ctime()
	thrs3=[]
	for i in range(10):
		t3=MyThread('delete')
		thrs3.append(t3)
	for n in range(10):
		thrs3[n].start()
	for j in range(10):
		thrs3[j].join()
	print 'end delete!'

        cur.execute('drop table if exists tdb')

if __name__ == '__main__':
	test_one_thread()
	test_ten_thread()
