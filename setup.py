import os
import sys
import subprocess

major_start_date='2017-06-27'

def find_git_executable():
    if os.name == 'nt':
        if 'PATH' in os.environ:
            for path in os.environ['PATH'].split(os.pathsep):
                git_path = os.path.join(path, 'git.exe')
                if os.path.isfile(git_path) and os.access(git_path, os.X_OK):
                    print("Windows Found git at: {}".format(git_path))
                    return git_path
    else:
        try:
            which_process = subprocess.Popen(["which", "git"], 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE)
            git_path, _ = which_process.communicate()
            if git_path:
                git_path = git_path.decode().strip()
                if os.path.isfile(git_path) and os.access(git_path, os.X_OK):
                    print("Found git at: {}".format(git_path))
                    return git_path
        except:
            pass

    print("Git executable not found")
    return None

if os.name == 'nt':
    from distutils.core import setup
    vs2017_path = os.environ.get('VS2017COMNTOOLS',
                            (r"C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\Common7\Tools"))
    os.environ['VS2017COMNTOOLS'] = vs2017_path
    os.environ['DISTUTILS_USE_SDK'] = '1'
    os.environ['MSSdk'] = '1'
    vs_link_path = r"C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Tools\MSVC\14.16.27023\bin\Hostx64\x64"
    os.environ['PATH'] = vs_link_path + os.pathsep + os.environ['PATH']
    include_path = r"C:\Program Files (x86)\Windows Kits\10\Include\10.0.19041.0\ucrt"
    os.environ['INCLUDE'] = include_path + os.pathsep + os.environ.get('INCLUDE', '')

if sys.version > '3':
    setup_file = "setup_3.py"
else:
    setup_file = "setup_2.py"

with open('VERSION', 'r') as file:
    version = file.readline().strip()

git_executable = find_git_executable()
serial_number = "0000"  # 기본값 설정

if git_executable:
    command = '"{}" rev-list --after={} --count HEAD'.format(git_executable, major_start_date)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0 and stdout:
        count = int(stdout.decode().strip())
        serial_number = "{:04d}".format(count)
        
    if stderr:
        print("Git command warning/error: {}".format(stderr.decode()))

python_version = version + "." + str(serial_number)

#os.system(setup_file)
setup_fh = open(setup_file)
setup_content = setup_fh.read()
setup_fh.close()
exec(setup_content, {'python_version':python_version, 'argv': sys.argv + ['arg1']})
