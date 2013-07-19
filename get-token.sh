#!/bin/bash


URL='https://trello.com/1/authorize?name=My+Test+Application&expiration=1day&response_type=token&scope=read,write&key='
APPKEY=$1

if [[ -z $APPKEY ]]; then
    echo "You need to provide a app key"
    echo "Maybe add an `echo appkey_file` as a n argument"
    exit 1
else
    echo $URL$APPKEY
fi
