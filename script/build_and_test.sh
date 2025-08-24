#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd -P )"
DRIVER_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_PATH=$(which python3.12)
PIP_PATH=$(which pip3.12)

function run_test1() {
    cd $DRIVER_ROOT/tests
    $PYTHON_PATH test_CUBRIDdb.py 
    cat test_CUBRIDdb.result >> $DRIVER_ROOT/test_result.log
    $PYTHON_PATH test_cubrid.py >> $DRIVER_ROOT/test_result.log
    cat test_cubrid.result >> $DRIVER_ROOT/test_result.log   
    $PYTHON_PATH test_CUBRIDdb_crud.py >> $DRIVER_ROOT/test_result.log
    cat test_CUBRIDdb_crud.result >> $DRIVER_ROOT/test_result.log
}

function run_test3() {
    cd $DRIVER_ROOT/tests3
    $PYTHON_PATH -m pytest >> $DRIVER_ROOT/test_result.log
}

echo "PIP_PATH: $PIP_PATH"
echo "PYTHON_PATH: $PYTHON_PATH"
echo "DRIVER_ROOT: $DRIVER_ROOT"
cd $DRIVER_ROOT

rm -rf $DRIVER_ROOT/dist
rm -rf $DRIVER_ROOT/build
rm -rf $DRIVER_ROOT/cubrid_python.egg-info

$PYTHON_PATH setup.py bdist_wheel

if [ -z "$INSTALL_WHEEL_PATH" ]; then
    INSTALL_WHEEL_PATH=$(find ./dist -name "cubrid_python-*.whl")
    echo "INSTALL_WHEEL_PATH: $INSTALL_WHEEL_PATH"
fi

$PIP_PATH uninstall cubrid_python -y

if [ -z "$INSTALL_WHEEL_PATH" ]; then
    echo "INSTALL_WHEEL_PATH is not set"
    exit 1
fi

$PIP_PATH install $INSTALL_WHEEL_PATH
rm $DRIVER_ROOT/test_result.log
run_test1
run_test3
# cat $DRIVER_ROOT/test_result.log
exit 0
