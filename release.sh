#!/bin/bash

arg=$@
shell_dir="$( cd "$( dirname "$0" )" && pwd -P )"
temp_dir=$shell_dir/temp_release
temp_python_dir=$temp_dir/cubrid-python
git_file=$(which git)
first_version_file=$temp_python_dir/VERSION
second_version_file=$shell_dir/VERSION
major_start_date='2017-06-27'


function show_usage ()
{
  echo "Usage: $0 [OPTIONS or Commit-ID]"
  echo "Note. For Python Driver Release"
  echo ""
  echo " OPTIONS"
  echo "  -? | -h Show this help message and exit"
  echo ""
  echo " Commit-ID"
  echo " Command) git resete --hard [Commit-ID]"
  echo "          git submodule update"
  echo ""
  echo " EXAMPLES"
  echo "  $0                                           # Compress "
  echo "  $0 a6ae44b76dc283bd74c555fef1585ed0ec7dc470  # Git Reset, Submodule Update and Compress"
  echo ""
}

while getopts "h" opt; do
  case $opt in
    h|\?|* ) show_usage; exit 1;;
  esac
done

if [ "x$git_file" = "x" ]; then
    echo "[ERROR] Git not found"
    exit 0
fi


if [ ! -z $arg ]; then
  echo "[CHECK] input commit id : $arg"
fi

if [ -f $1st_version_file ]; then
  echo "[CHECK] 1st version file : $first_version_file"
  VERSION=$(cat $first_version_file)
else
  echo "[CHECK] 2nd version file : $second_version_file"
  VERSION=$(cat $second_version_file)
fi

echo "Python Driver Version is $VERSION"
FOLDER_NAME=RB-$VERSION

if [ -d $temp_dir ]; then
  rm -rf $temp_dir
fi

mkdir -p $temp_dir
cd $temp_dir

git clone git@github.com:CUBRID/cubrid-python.git --recursive

if [ ! -z $arg ]; then
  echo "[CHECK] input commit id : $arg"
  cd $temp_python_dir
  git reset --hard $arg
  git submodule update
fi

cd $temp_python_dir
SERIAL_NUMBER=$(git rev-list --after $major_start_date --count HEAD | awk '{ printf "%04d", $1 }' 2> /dev/null)

cd $temp_dir
rm -rf $temp_dir/cubrid-python/.git
rm -rf $temp_dir/cubrid-python/cci-src/.git

mv cubrid-python $FOLDER_NAME
tar zcvf cubrid-python-$VERSION.$SERIAL_NUMBER.tar.gz $FOLDER_NAME
mv cubrid-python-$VERSION.$SERIAL_NUMBER.tar.gz $shell_dir
rm -rf $temp_dir

echo "SERIAL_NUMBER : $SERIAL_NUMBER"
echo "VERION $VERSION.$SERIAL_NUMBER Completed"
