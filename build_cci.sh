#!/bin/bash

#echo "build_cci sh."
if [ -f cci-src/cci/.libs/libcascci.a ];then
#  echo "libcascci.a exist."
  exit 0
fi

cd cci-src

rm -rf build_x86_64_release
mkdir -p build_x86_64_release

if [ "$1" = 'x86' ];then
  echo "32bit Driver not support"
  exit 9
elif [ "$1" = 'clean' ];then
  echo "clean build"
  rm -rf build_x86_64_release
  mkdir -p build_x86_64_release
  exit 0
else
  sh build.sh
fi
