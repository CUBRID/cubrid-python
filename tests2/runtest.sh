#!/bin/bash
rm -rf memoryLeaklog
mkdir  memoryLeaklog
rm -rf function_result
mkdir  function_result

db=pydb
cubrid createdb -r $db
cubrid server start $db
cubrid broker start
echo "Python DBI Test Begin..."

brokerPort=`cubrid broker status -b|grep broker1|awk '{print $4}'`
#a=`cat /etc/sysconfig/network-scripts/ifcfg-eth1|grep IPADDR|awk '{print $1}'`
a=`/sbin/ifconfig | grep inet | grep -v 127 | awk '{print $2}' | sed 's/addr://g'|sed -n '1p'`
ipaddress="${a#*=}"

cd ./configuration
echo "<PythonConfig>" >python_config.xml
echo "  <ip>localhost</ip>" >> python_config.xml
echo "  <port>$brokerPort</port>"   >>python_config.xml
echo "  <dbname>$db</dbname>"  >>python_config.xml
echo "  <remoteIP>$ipaddress</remoteIP>"  >>python_config.xml
echo "</PythonConfig>" >>python_config.xml
cd ..

ls |grep -E "^_" |grep  -v "runTest.sh" | grep -v "CUBRID_Python.list_file" > ./memoryLeaklog/CUBRID_Python.list_file
while read LIST_FILE
do
   cd $LIST_FILE
   ls |grep -E ".py$" > ./../memoryLeaklog/$LIST_FILE.list
   
   while read TEST_FILE
   do 
      valgrind --leak-check=full --log-file=./../memoryLeaklog/$TEST_FILE.memoryleak python $TEST_FILE >>./../function_result/$TEST_FILE.result 2>&1
   done < ./../memoryLeaklog/$LIST_FILE.list
   
   cd ..

done < ./memoryLeaklog/CUBRID_Python.list_file

cubrid server stop $db
cubrid broker stop
cubrid deletedb $db

rm -rf lob
rm ./memoryLeaklog/*.list
rm ./memoryLeaklog/CUBRID_Python.list_file
echo "Python DBI Test End"


