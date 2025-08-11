@echo off
setlocal enabledelayedexpansion

rem Set variables
set ARG=%*
set SHELL_DIR=%~dp0
set SHELL_DIR=%SHELL_DIR:"=%
set TEMP_DIR=%SHELL_DIR%\temp_release
set TEMP_PYTHON_DIR=%TEMP_DIR%\cubrid-python
set GIT_PATH=C:\Program Files\Git\bin\git.exe
set FIRST_VERSION_FILE=%TEMP_PYTHON_DIR%\VERSION
set SECOND_VERSION_FILE=%SHELL_DIR%\VERSION
rem set GIT_SOURCE=https://github.com/CUBRID/cubrid-python.git
set GIT_SOURCE=git@github.com:hwany7seo/cubrid-python.git --recursive -b 3_10_test
set MAJOR_START_DATE=2017-06-27

set PYTHON_EXECUTE_END=4
set PYTHON_EXECUTE[0]=C:\python\python36
set PYTHON_EXECUTE[1]=C:\python\python310
set PYTHON_EXECUTE[2]=C:\python\python311
set PYTHON_EXECUTE[3]=C:\python\python312
set /a PYTHON_COUNT=0

:main
echo %TEMP_PYTHON_DIR%

if not "%ARG%"=="" (
    if "%ARG%"=="-h" (
        call :show_usage
        exit /b 0
    )
)

if not exist "%GIT_PATH%" (
    echo [ERROR] Git not found
    exit /b 1
)

rem Initialize temp directory
if exist "%TEMP_DIR%" (
    rmdir /s /q "%TEMP_DIR%"
)

mkdir "%TEMP_DIR%"
cd /d "%TEMP_DIR%"

echo "source download"
"%GIT_PATH%" clone %GIT_SOURCE% --recursive

echo "Handle commit ID if provided"
if not "%ARG%"=="" (
    echo [CHECK] input commit id: %ARG%
    cd /D "%TEMP_PYTHON_DIR%"
    "%GIT_PATH%" reset --HARD %ARG%
    "%GIT_PATH%" submodule update
)

if exist "%FIRST_VERSION_FILE%" (
    echo [CHECK] 1st version file: %FIRST_VERSION_FILE%
    for /f "usebackq tokens=*" %%a in ("%FIRST_VERSION_FILE%") do set VERSION=%%a
) else if exist "%SECOND_VERSION_FILE%" (
    echo [CHECK] 2nd version file: %SECOND_VERSION_FILE%
    for /f "usebackq tokens=*" %%a in (%SECOND_VERSION_FILE%) do set VERSION=%%a
) else (
    echo [ERROR] Version file not found
    exit /b 1
)

call :check_version
call :build_env
call :build
call :uninstall_driver
call :install_driver
call :run_testcase
exit /b 0

:check_version
echo "Check Version"
cd /d "%TEMP_DIR%\cubrid-python"
if exist "%FIRST_VERSION_FILE%" (
    echo [CHECK] 1st version file: %FIRST_VERSION_FILE%
    for /f "usebackq tokens=*" %%a in ("%FIRST_VERSION_FILE%") do set VERSION=%%a
) else if exist "%SECOND_VERSION_FILE%" (
    echo [CHECK] 2nd version file: %SECOND_VERSION_FILE%
    for /f "usebackq tokens=*" %%a in (%SECOND_VERSION_FILE%) do set VERSION=%%a
) else (
    echo [ERROR] Version file not found
    exit /b 1
)
for /f "delims=" %%a in ('"%GIT_PATH%" rev-list --count --after=%MAJOR_START_DATE% HEAD') do (
    set SERIAL_NUMBER=%%a
)

set DRIVER_VERSION=%VERSION%.%SERIAL_NUMBER%
echo [CHECK] Driver version: %DRIVER_VERSION%
set PYTHON_WHEEL[0]=CUBRID_Python-%DRIVER_VERSION%-cp36-cp36m-win_amd64.whl
set PYTHON_WHEEL[1]=CUBRID_Python-%DRIVER_VERSION%-cp310-cp310-win_amd64.whl
set PYTHON_WHEEL[2]=CUBRID_Python-%DRIVER_VERSION%-cp311-cp311-win_amd64.whl
set PYTHON_WHEEL[3]=cubrid_python-%DRIVER_VERSION%-cp312-cp312-win_amd64.whl
exit /b 0




:build_env
echo "Execute ENV Batch For Windows"
call "%SHELL_DIR%\..\env_windows.bat"
exit /b 0

:build
rem Driver Build
echo "Driver Build"
cd /d "%TEMP_DIR%\cubrid-python"
if %PYTHON_COUNT% lss %PYTHON_EXECUTE_END% (
    echo "BUILD !PYTHON_EXECUTE[%PYTHON_COUNT%]!\python.exe"
    call "%%PYTHON_EXECUTE[%PYTHON_COUNT%]%%\python.exe" setup.py bdist_wheel
    set /a PYTHON_COUNT+=1
    goto build
)
set /a PYTHON_COUNT=0
echo "Driver Build End"
exit /b 0

:uninstall_driver
rem Driver Uninstall
echo "Driver Uninstall"
cd /d "%TEMP_DIR%\cubrid-python"
if %PYTHON_COUNT% lss %PYTHON_EXECUTE_END% (
    echo "UNINSTALL !PYTHON_EXECUTE[%PYTHON_COUNT%]!\Scripts\pip.exe"
    call "%%PYTHON_EXECUTE[%PYTHON_COUNT%]%%\Scripts\pip.exe" uninstall CUBRID-Python -y
    set /a PYTHON_COUNT+=1
    goto uninstall_driver
)
set /a PYTHON_COUNT=0
exit /b 0

:install_driver
rem Driver Install
echo "Driver Install"
cd /d "%TEMP_DIR%\cubrid-python\dist"
if %PYTHON_COUNT% lss %PYTHON_EXECUTE_END% (
    echo "INSTALL !PYTHON_EXECUTE[%PYTHON_COUNT%]!\Scripts\pip.exe"
    call "%%PYTHON_EXECUTE[%PYTHON_COUNT%]%%\Scripts\pip.exe" install !PYTHON_WHEEL[%PYTHON_COUNT%]!
    set /a PYTHON_COUNT+=1
    goto install_driver
)
set /a PYTHON_COUNT=0
exit /b 0

:run_testcase
echo "Run Testcase"
cd /d "%TEMP_DIR%\cubrid-python\tests"
if %PYTHON_COUNT% lss %PYTHON_EXECUTE_END% (
    echo "RUN !PYTHON_EXECUTE[%PYTHON_COUNT%]!\python.exe" >> test_python.log
    call "%%PYTHON_EXECUTE[%PYTHON_COUNT%]%%\python.exe" test_cubrid.py
    call type test_cubrid.result >> test_python.log
    call "%%PYTHON_EXECUTE[%PYTHON_COUNT%]%%\python.exe" test_CUBRIDdb.py
    call type test_CUBRIDdb.result >> test_python.log
    set /a PYTHON_COUNT+=1
    goto run_testcase
)
set /a PYTHON_COUNT=0
call type test_python.log
exit /b 0

:show_usage
echo Usage: %0 [OPTIONS or Commit-ID]
echo Note. For Python Driver Release
echo.
echo OPTIONS
echo   -? ^| -h Show this help message and exit
echo.
echo Commit-ID
echo Command) git reset --hard [Commit-ID]
echo           git submodule update
echo.
echo EXAMPLES
echo   %0                                           # Compress
echo   %0 a6ae44b76dc283bd74c555fef1585ed0ec7dc470  # Git Reset, Submodule Update and Compress
exit /b 1

