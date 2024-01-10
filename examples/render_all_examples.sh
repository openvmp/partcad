#!/bin/sh

for i in part_* assembly_* export; do
    echo "Rendering $i..."
    (cd $i && pc render)
done
