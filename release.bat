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
set GIT_SOURCE=https://github.com/CUBRID/cubrid-python.git
set MAJOR_START_DATE=2017-06-27



set PYTHON_EXECUTE_END=6
set PYTHON_EXECUTE[0]=C:\python\python26\python.exe
set PYTHON_EXECUTE[1]=C:\python\python27\python.exe
set PYTHON_EXECUTE[2]=C:\python\python30\python.exe
set PYTHON_EXECUTE[3]=C:\python\python31\python.exe
set PYTHON_EXECUTE[4]=C:\python\python32\python.exe
set PYTHON_EXECUTE[5]=C:\python\python36\python.exe
set /a PYTHON_COUNT=0

set BUILD_FOLDERS=lib.win-amd64-2.6 lib.win-amd64-2.7 lib.win-amd64-3.0 lib.win-amd64-3.1 lib.win-amd64-3.2 lib.win-amd64-3.6

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

:build_env
echo "Execute ENV Batch For Windows"
call "%SHELL_DIR%\env_windows.bat"

:build
rem Driver Build
echo "Driver Build"
cd /d "%TEMP_DIR%\cubrid-python"
if %PYTHON_COUNT% lss %PYTHON_EXECUTE_END% (
    echo "BUILD %%PYTHON_EXECUTE[%PYTHON_COUNT%]%%"
    call "%%PYTHON_EXECUTE[%PYTHON_COUNT%]%%" setup.py build
    set /a PYTHON_COUNT+=1
    goto build
)

:zip
echo Python Driver Version is %VERSION%
set FOLDER_NAME=RB-%VERSION%

cd /d "%TEMP_PYTHON_DIR%"
for /f "delims=" %%a in ('"%GIT_PATH%" rev-list --count --after=%MAJOR_START_DATE% HEAD') do (
    set SERIAL_NUMBER=%%a
)
set SERIAL_NUMBER=0000%SERIAL_NUMBER%
set SERIAL_NUMBER=%SERIAL_NUMBER:~-4%
set DRIVER_VERSION=%VERSION%.%SERIAL_NUMBER%

REM Compress and move files
echo "%TEMP_PYTHON_DIR%\build"
cd /d "%TEMP_PYTHON_DIR%\build"
ls

for %%F in (%BUILD_FOLDERS%) do (
    echo Processing %%F
    set "PYTHON_VERSION=%%F"

    if not exist "%FOLDER_NAME%" (
        echo "create dir %FOLDER_NAME%"
        mkdir "%FOLDER_NAME%"
        ls
    ) else (
        echo "exist dir"
        rmdir /s /q "%FOLDER_NAME%"
        mkdir "%FOLDER_NAME%"
    )

    xcopy "%%F\*" "%FOLDER_NAME%" /E /I /H /C /Y

    set "PYTHON_VERSION=!PYTHON_VERSION:~-3,3!"
    set "PYTHON_VERSION=!PYTHON_VERSION:.=!"
    echo "!PYTHON_VERSION!"
    echo "%DRIVER_VERSION%"

    powershell -Command Compress-Archive -Path "%FOLDER_NAME%" -DestinationPath "CUBRID-!DRIVER_VERSION!-windows-python!PYTHON_VERSION!-amd64.zip"
    rmdir /s /q "%FOLDER_NAME%"
)

echo SERIAL_NUMBER: %SERIAL_NUMBER%
echo VERSION %VERSION%.%SERIAL_NUMBER% Completed

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

