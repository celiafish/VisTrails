#!/bin/bash
SRC_PATH="vistrails"
BIN_PATH="Contents/Resources/lib/python2.5"
DIRS="api core db gui packages tests"

if [ -z "$1" ] || [ -z "$2" ]
then
    echo "usage: $0 <src_dir> <bin_dir>"
    exit 65
fi

for dir in $DIRS
do
    if [ -e "$2/$BIN_PATH/$dir" ]
    then
	rm -r $2/$BIN_PATH/$dir
    fi
    ln -s $1/$SRC_PATH/$dir $2/$BIN_PATH/$dir
done

if [ -e "$2/$BIN_PATH/../../vistrails.py" ]
then
    rm $2/$BIN_PATH/../../vistrails.py
fi
ln -s $1/$SRC_PATH/vistrails.py $2/$BIN_PATH/../../vistrails.py

exit 0