#!/bin/bash

ARG="$*"
SHELL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP_DIR="$SHELL_DIR/temp_release"
TEMP_PYTHON_DIR="$TEMP_DIR/cubrid-python"
RELEASE_FOLDER="$SHELL_DIR/release"
GIT_PATH="$(which git)"
FIRST_VERSION_FILE="$TEMP_PYTHON_DIR/VERSION"
SECOND_VERSION_FILE=$(dirname "$SHELL_DIR")/VERSION
GIT_SOURCE="https://github.com/CUBRID/cubrid-python.git"
MAJOR_START_DATE="2017-06-27"

PYTHON_EXECUTE_END=4
PYTHON_PATH[0]=$(which python3.6)
PYTHON_PATH[1]=$(which python3.10)
PYTHON_PATH[2]=$(which python3.11)
PYTHON_PATH[3]=$(which python3.12)

PIP_PATH[0]=$(which pip3.6)
PIP_PATH[1]=$(which pip3.10)
PIP_PATH[2]=$(which pip3.11)
PIP_PATH[3]=$(which pip3.12)

PYTHON_COUNT=0

TESTCASE_RESULT_FILE="$TEMP_DIR/linux_test_python_result.log"

# Main function
main() {
    echo "$TEMP_PYTHON_DIR"

    if [ -n "$ARG" ]; then
        if [ "$ARG" = "-h" ] || [ "$ARG" = "-?" ]; then
            show_usage
            exit 0
        fi
    fi

    if [ ! -x "$GIT_PATH" ]; then
        echo "[ERROR] Git not found"
        exit 1
    fi

    
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi

    mkdir -p "$TEMP_DIR"
    cd "$TEMP_DIR"

    echo "source download"
    $GIT_PATH clone $GIT_SOURCE --recursive

    echo "Handle commit ID if provided"
    if [ -n "$ARG" ]; then
        echo "[CHECK] input commit id: $ARG"
        cd "$TEMP_PYTHON_DIR"
        $GIT_PATH reset --hard "$ARG"
        $GIT_PATH submodule update
    fi

    if [ -f "$FIRST_VERSION_FILE" ]; then
        echo "[CHECK] 1st version file: $FIRST_VERSION_FILE"
        VERSION=$(cat "$FIRST_VERSION_FILE")
    elif [ -f "$SECOND_VERSION_FILE" ]; then
        echo "[CHECK] 2nd version file: $SECOND_VERSION_FILE"
        VERSION=$(cat "$SECOND_VERSION_FILE")
    else
        echo "[ERROR] Version file not found"
        exit 1
    fi

    check_version
    build
    copy_to_release_folder
    extract_zip_and_targz
    uninstall_driver
    install_driver
    run_testcase
    run_testcase_3
    if [ -f "$TESTCASE_RESULT_FILE" ]; then
        echo "Testcase Result: $TESTCASE_RESULT_FILE"
        cat "$TESTCASE_RESULT_FILE"
    fi
    exit 0
}

# Check version function
check_version() {
    echo "Check Version"
    cd "$TEMP_DIR/cubrid-python"
    
    if [ -f "$FIRST_VERSION_FILE" ]; then
        echo "[CHECK] 1st version file: $FIRST_VERSION_FILE"
        VERSION=$(cat "$FIRST_VERSION_FILE")
    elif [ -f "$SECOND_VERSION_FILE" ]; then
        echo "[CHECK] 2nd version file: $SECOND_VERSION_FILE"
        VERSION=$(cat "$SECOND_VERSION_FILE")
    else
        echo "[ERROR] Version file not found"
        exit 1
    fi
    
    SERIAL_NUMBER=$($GIT_PATH rev-list --count --after="$MAJOR_START_DATE" HEAD)
    
    DRIVER_VERSION="$VERSION.$SERIAL_NUMBER"
    echo "[CHECK] Driver version: $DRIVER_VERSION"
    
    PYTHON_WHEEL[0]="cubrid_python-$DRIVER_VERSION-cp36-cp36m-linux_x86_64.whl"
    PYTHON_WHEEL[1]="cubrid_python-$DRIVER_VERSION-cp310-cp310-linux_x86_64.whl"
    PYTHON_WHEEL[2]="cubrid_python-$DRIVER_VERSION-cp311-cp311-linux_x86_64.whl"
    PYTHON_WHEEL[3]="cubrid_python-$DRIVER_VERSION-cp312-cp312-linux_x86_64.whl"
}

# Build function
build() {
    echo "Driver Build"
    cd "$TEMP_DIR/cubrid-python"
    
    while [ $PYTHON_COUNT -lt $PYTHON_EXECUTE_END ]; do
        echo "BUILD ${PYTHON_PATH[$PYTHON_COUNT]}"
        "${PYTHON_PATH[$PYTHON_COUNT]}" setup.py bdist_wheel
        PYTHON_COUNT=$((PYTHON_COUNT + 1))
    done
    
    PYTHON_COUNT=0
    echo "Driver Build End"
}

# Copy to release folder function
copy_to_release_folder() {
    echo "Copy to Release Folder"
    cd "$TEMP_DIR/cubrid-python/dist"

    if [ -d "$RELEASE_FOLDER" ]; then
        rm -rf "$RELEASE_FOLDER"
    fi

    mkdir -p "$RELEASE_FOLDER"
    cp *.whl "$RELEASE_FOLDER"
}

extract_zip_and_targz() {
    echo "Extract Targz"
    cd "$TEMP_DIR"
    tar zcvf "$RELEASE_FOLDER/cubrid-python-${VERSION}.tar.gz" \
     --exclude='.git' --exclude='.gitignore' --exclude='.gitmodules' \
     --exclude='build' --exclude='dist' --exclude='*.egg-info' \
     --exclude='cci-src/build_x86_64_release' \
     cubrid-python

    echo "Extract zip"
    cd "$TEMP_DIR"
    zip -r "$RELEASE_FOLDER/cubrid-python-${VERSION}.zip" cubrid-python \
     -x "*.git*" "*.gitignore" "*.gitmodules" \
     "*/build/*" "*/dist/*" "*.egg-info*" \
     "*/cci-src/build_x86_64_release/*"
}


# Uninstall driver function
uninstall_driver() {
    echo "Driver Uninstall"
    cd "$TEMP_DIR/cubrid-python"
    
    while [ $PYTHON_COUNT -lt $PYTHON_EXECUTE_END ]; do
        echo "UNINSTALL ${PIP_PATH[$PYTHON_COUNT]}"
        "${PIP_PATH[$PYTHON_COUNT]}" uninstall CUBRID-Python -y
        PYTHON_COUNT=$((PYTHON_COUNT + 1))
    done
    PYTHON_COUNT=0
}

# Install driver function
install_driver() {
    echo "Driver Install"
    cd "$TEMP_DIR/cubrid-python/dist"
    
    while [ $PYTHON_COUNT -lt $PYTHON_EXECUTE_END ]; do
        echo "INSTALL ${PIP_PATH[$PYTHON_COUNT]}"
        if [ $PYTHON_COUNT -eq 0 ]; then
            "${PIP_PATH[$PYTHON_COUNT]}" install --user "${PYTHON_WHEEL[$PYTHON_COUNT]}"
        else
            "${PIP_PATH[$PYTHON_COUNT]}" install "${PYTHON_WHEEL[$PYTHON_COUNT]}"
        fi
        PYTHON_COUNT=$((PYTHON_COUNT + 1))
    done
    
    PYTHON_COUNT=0
}

# Run testcase function
run_testcase() {
    echo "Run Testcase"
    cd "$TEMP_DIR/cubrid-python/tests"
    
    while [ $PYTHON_COUNT -lt $PYTHON_EXECUTE_END ]; do
        echo "RUN ${PYTHON_PATH[$PYTHON_COUNT]}" >> "$TESTCASE_RESULT_FILE"
        "${PYTHON_PATH[$PYTHON_COUNT]}" test_cubrid.py
        cat test_cubrid.result >> "$TESTCASE_RESULT_FILE"
        "${PYTHON_PATH[$PYTHON_COUNT]}" test_CUBRIDdb.py
        cat test_CUBRIDdb.result >> "$TESTCASE_RESULT_FILE"
        "${PYTHON_PATH[$PYTHON_COUNT]}" test_CUBRIDdb_crud.py
        cat test_CUBRIDdb_crud.result >> "$TESTCASE_RESULT_FILE"
        PYTHON_COUNT=$((PYTHON_COUNT + 1))
    done
    
    PYTHON_COUNT=0
}

run_testcase_3() {
    echo "Run Testcase 3"
    cd "$TEMP_DIR/cubrid-python/tests3"

    while [ $PYTHON_COUNT -lt $PYTHON_EXECUTE_END ]; do
        echo "RUN ${PYTHON_PATH[$PYTHON_COUNT]}" >> "$TESTCASE_RESULT_FILE"
        "${PYTHON_PATH[$PYTHON_COUNT]}" -m pytest >> "$TESTCASE_RESULT_FILE"
        PYTHON_COUNT=$((PYTHON_COUNT + 1))
    done

    PYTHON_COUNT=0
}

# Show usage function
show_usage() {
    echo "Usage: $0 [OPTIONS or Commit-ID]"
    echo "Note. For Python Driver Release"
    echo ""
    echo "OPTIONS"
    echo "  -? | -h Show this help message and exit"
    echo ""
    echo "Commit-ID"
    echo "Command) git reset --hard [Commit-ID]"
    echo "         git submodule update"
    echo ""
    echo "EXAMPLES"
    echo "  $0                                           # Compress"
    echo "  $0 a6ae44b76dc283bd74c555fef1585ed0ec7dc470  # Git Reset, Submodule Update and Compress"
}

echo "Start Test Release"
main "$@"
