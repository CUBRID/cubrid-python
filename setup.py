import os
import sys
import subprocess

major_start_date='2017-06-27'

print('Python version_info:', sys.version_info)

if sys.version_info.major < 3:
    import io

if 'bdist_wheel' in sys.argv[1:]:
    try:
        import wheel
    except ImportError:
        print("wheel is not installed. Please install wheel to build the wheel.")
        sys.exit(1)

if os.name == 'nt':
    if sys.version_info.minor >= 6:
        from setuptools import setup
    else:
        from distutils.core import setup
    
    print("Setting up Visual Studio environment...")
    
    os.environ['DISTUTILS_USE_SDK'] = '1'
    os.environ['MSSdk'] = '1'
    
    vs2017_path = r"C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Tools\MSVC\14.16.27023"
    if os.path.exists(vs2017_path):
        os.environ['PATH'] = os.path.join(vs2017_path, "bin", "Hostx64", "x64") + os.pathsep + os.environ['PATH']
        os.environ['INCLUDE'] = os.path.join(vs2017_path, "include") + os.pathsep + os.environ.get('INCLUDE', '')
        os.environ['LIB'] = os.path.join(vs2017_path, "lib", "x64") + os.pathsep + os.environ.get('LIB', '')
        print(f"Using Visual Studio 2017 at: {vs2017_path}")
    else:
        print("Visual Studio 2017 not found, using system PATH")
    
    sdk_path = r"C:\Program Files (x86)\Windows Kits\10\Include\10.0.19041.0"
    if os.path.exists(sdk_path):
        os.environ['INCLUDE'] = os.path.join(sdk_path, "shared") + os.pathsep + os.environ.get('INCLUDE', '')
        os.environ['INCLUDE'] = os.path.join(sdk_path, "ucrt") + os.pathsep + os.environ.get('INCLUDE', '')
        os.environ['INCLUDE'] = os.path.join(sdk_path, "um") + os.pathsep + os.environ.get('INCLUDE', '')
        print(f"Using Windows SDK at: {sdk_path}")
    else:
        print("Windows SDK not found, using system INCLUDE")
    
    sdk_lib_path = r"C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0"
    if os.path.exists(sdk_lib_path):
        os.environ['LIB'] = os.path.join(sdk_lib_path, "ucrt", "x64") + os.pathsep + os.environ.get('LIB', '')
        os.environ['LIB'] = os.path.join(sdk_lib_path, "um", "x64") + os.pathsep + os.environ.get('LIB', '')
        print(f"Using Windows SDK lib at: {sdk_lib_path}")
    else:
        print("Windows SDK lib not found, using system LIB")
    
    sdk_bin_path = r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64"
    if os.path.exists(sdk_bin_path):
        os.environ['PATH'] = sdk_bin_path + os.pathsep + os.environ['PATH']
        print(f"Using Windows SDK bin at: {sdk_bin_path}")
    else:
        print("Windows SDK bin not found, using system PATH")

if sys.version_info.major >= 3:
    setup_file = "setup_3.py"
else:
    setup_file = "setup_2.py"

with open('VERSION', 'r') as file:
    version = file.readline().strip()

command = "git rev-list --after={0} --count HEAD | awk '{{ printf \"%04d\", $1 }}'".format(major_start_date)
process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = process.communicate()
if process.returncode == 0:
    serial_number = stdout.decode().strip()

driver_version = version + "." + str(serial_number)

if str(serial_number) == '':
    print('using version.h')
    with open('cubrid_ext/version.h', 'r', encoding='utf-8') as file:
        driver_version = file.read().split('"')[1]
else:
    print('using version.h.template')
    if sys.version_info.major >= 3:
        with open('cubrid_ext/version.h.template', 'r', encoding='utf-8') as file:
            template_content = file.read()
        with open('cubrid_ext/version.h', 'w', encoding='utf-8') as file:
            file.write(template_content.replace('{{VERSION}}', driver_version))
    else:
        with io.open('cubrid_ext/version.h.template', 'r', encoding='utf-8') as file:
            template_content = file.read()
        with io.open('cubrid_ext/version.h', 'w', encoding='utf-8') as file:
            file.write(template_content.replace('{{VERSION}}', driver_version))

#os.system(setup_file)
if sys.version_info.major >= 3:
    setup_fh = open(setup_file, encoding='utf-8')
else:
    setup_fh = open(setup_file)
setup_content = setup_fh.read()
setup_fh.close()
exec(setup_content, {'driver_version':driver_version, 'argv': sys.argv + ['arg1']})
