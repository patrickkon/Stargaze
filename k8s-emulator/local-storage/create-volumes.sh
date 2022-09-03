#!/bin/bash
set -e

for i in `seq 1 10`; do
    srcdir="/mnt/local-storage-srcs/vol${i}"
    dstdir="/mnt/local-storage/vol${i}"
    mkdir -p ${srcdir}
    mkdir -p ${dstdir}
    mount --bind ${srcdir} ${dstdir}
done
