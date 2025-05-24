#!/usr/bin/env bash

docker build --build-arg SCRIPT_DIRECTORY=$PWD -t binwalkv3 .

