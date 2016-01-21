#!/bin/bash

#echo "build_cci sh."
if [ -f cci-src/cci/.libs/libcascci.a ];then
#  echo "libcascci.a exist."
  exit 0
fi

tar xvjf cci-src.tar.bz2
cd cci-src
chmod +x configure
chmod +x external/libregex38a/configure
chmod +x external/libregex38a/install-sh
if [ "$1" = 'x86' ];then
  ./configure 
else
  ./configure --enable-64bit 
fi

make
