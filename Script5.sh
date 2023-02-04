#!/bin/sh
#This script is to make variable read only, means we cannot set the value of NAME variable again
NAME=Warrior
readonly NAME
NAME=Premkumar
echo "my name is: $NAME"
