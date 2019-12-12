#!/bin/bash
. ./init.sh

db=pydb
CUBRID_LANG=ko_KR.utf8
PYTHON_CON=configuration/python_config.xml
TC_DIR_PERFORMANCE="performance"
TC_DIR="python"
testcases=python_testcase_list
MEM_LOG=memoryLeaklog
FUNC_LOG=function_result
VALGRIND="valgrind --leak-check=full"
python="python"
test_mode="normal"
test_case="functional_only"

rm -rf memoryLeaklog
mkdir  memoryLeaklog
rm -rf function_result
mkdir  function_result

get_options "$@"

python_version_major=$(python_version_check $python)

if [ x"$python_version_major" != "x2" ];then
	echo -n "We do not support this version: "
	$python --version
	exit
fi

echo "Python DBI Test Begin... ($python), test_mode = $test_mode, test_case = $test_case"

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
	if [ $test_mode = "normal" ];then
		$python $tc >> $FUNC_LOG/$tcb.result 2>&1
	else
		$VALGRIND --log-file=$MEM_LOG/$tcb.memLeak $python $tc >> $FUNC_LOG/$tcb.result 2>&1
	fi
	verdict=$(check_verdict $FUNC_LOG/$tcb.result)
	echo $verdict
done

if [ "$test_case" != "functional_only" ];then
	echo "Run Performance Test"
	for tc in $TC_DIR_PERFORMANCE/*
	do
		$python $tc
	done
fi

cubrid server stop $db
cubrid deletedb $db
rm -f $testcases
rm -rf lob

echo "Python DBI Test End"
