#!/bin/sh

for i in produce_* feature_export; do
    echo "Rendering $i..."
    (cd $i && pc render)
done
