#!/bin/bash

for i in `lxc-ls`
do lxc-destroy -f -n $i
done
