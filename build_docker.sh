#!/usr/bin/env bash

docker build --build-arg SCRIPT_DIRECTORY="$(pwd)" -t binwalkv3 .

