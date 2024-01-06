#!/bin/sh

for i in part_* assembly_*; do
    echo "Rendering $i..."
    (cd $i && pc render)
done
