echo arg is :%1%
cd cci-src\win\cas_cci

call "%VS90COMNTOOLS%vsvars32.bat"
if "%1%"=="x86" (
devenv cas_cci_v140_lib.vcxproj /build "Release"
) else ( 
devenv cas_cci.vcproj /build "release|x64" 
)
cd ..\..\..
