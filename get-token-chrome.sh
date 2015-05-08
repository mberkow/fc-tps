#!/bin/bash


URL='https://trello.com/1/authorize?name=TPS+Report&expiration=1day&response_type=token&scope=read,write&key='

if [[ -z $1 ]]; then
    APPKEY=`grep apikey config.json  | awk -F\: '{print $2}' | sed s/[\"\,]//g`
else
    APPKEY=$1
fi

if [[ -z $APPKEY ]]; then
    echo "You need to provide a app key"
    echo "Maybe add an `echo appkey_file` as a n argument"
    exit 1
else
    echo open -a /Applications/Google\\ Chrome.app \'$URL$APPKEY\'
fi
