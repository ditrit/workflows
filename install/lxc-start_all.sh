#!/bin/bash

for i in `lxc-ls`
do lxc-start -d -n $i
done
