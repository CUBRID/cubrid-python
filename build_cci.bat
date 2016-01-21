echo arg is :%1%
rd /s/q cci-src
7z x cci-src.tar.bz2
7z x cci-src.tar
cd cci-src\win\cas_cci

call "%VS90COMNTOOLS%vsvars32.bat"
if "%1%"=="x86" (
devenv cas_cci.vcproj /build "release|Win32" 
) else ( 
devenv cas_cci.vcproj /build "release|x64" 
)
cd ..\..\..