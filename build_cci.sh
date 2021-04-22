#!/bin/bash

#echo "build_cci sh."
if [ -f cci-src/cci/.libs/libcascci.a ];then
#  echo "libcascci.a exist."
  exit 0
fi

cd cci-src
chmod +x configure
touch configure.ac
if [ "$1" = 'x86' ];then
  ./configure 
else
  ./configure --enable-64bit 
fi

make
