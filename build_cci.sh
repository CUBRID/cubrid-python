#!/bin/bash

#echo "build_cci sh."
if [ -f cci-src/cci/.libs/libcascci.a ];then
#  echo "libcascci.a exist."
  exit 0
fi

cd cci-src
if [ "$1" = 'x86' ];then
  echo "32bit Driver not support"
  exit 9
else
  sh build.sh
fi
