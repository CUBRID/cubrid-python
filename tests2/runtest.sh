#!/bin/bash
. ./init.sh

db=pydb
CUBRID_LANG=ko_KR.utf8
PYTHON_CON=configuration/python_config.xml
#TC_DIR="python performance"
TC_DIR="python"
testcases=python_testcase_list
MEM_LOG=memoryLeaklog
FUNC_LOG=function_result
VALGRIND="valgrind --leak-check=full"

rm -rf memoryLeaklog
mkdir  memoryLeaklog
rm -rf function_result
mkdir  function_result

PYTHON=$(find_python $*)

python_version_major=$(python_version_check $PYTHON)

if [ x"$python_version_major" != "x2" ];then
	echo -n "We do not support this version: "
	$PYTHON --version
	exit
fi

echo "Python DBI Test Begin... ($PYTHON)"

cubrid server stop $db
cubrid createdb $db $CUBRID_LANG
cubrid server restart $db
cubrid server restart demodb
cubrid broker restart
brokerPort=`cubrid broker status -b|grep broker1|awk '{print $4}'`
ipaddress=$(hostname -i)


echo "<PythonConfig>"			>  $PYTHON_CON
echo "  <ip>localhost</ip>"		>> $PYTHON_CON
echo "  <port>$brokerPort</port>"	>> $PYTHON_CON
echo "  <dbname>$db</dbname>"		>> $PYTHON_CON
echo "  <remoteIP>$ipaddress</remoteIP>">> $PYTHON_CON
echo "</PythonConfig>"			>> $PYTHON_CON

# Generate test cases from directories
rm -f $testcases
for dir in $TC_DIR
do
	find $dir -name '*.py' -print >> $testcases
done

for tc in $(cat $testcases)
do
	tcb=$(basename $tc)
	echo -n "Running TestCase ($tcb) $tc "
	$VALGRIND --log-file=$MEM_LOG/$tcb.memLeak $PYTHON $tc >> $FUNC_LOG/$tcb.result 2>&1
	verdict=$(check_verdict $FUNC_LOG/$tcb.result)
	echo $verdict
done

cubrid server stop $db
cubrid deletedb $db
rm -f $testcases
rm -rf lob

echo "Python DBI Test End"
