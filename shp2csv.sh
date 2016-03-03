#!/bin/bash

for D in `find data -type d`
do

    echo $D
    county=${D##*/}
    echo $county

    rm ${D}/${county}_addresses.csv

    ogr2ogr -f csv \
      ${D}/${county}_addresses.csv \
      ${D}/${county}_addresses.shp ${county}_addresses \
      -lco GEOMETRY=AS_XYZ

    echo ${D}/${county}_addresses.csv

    sed -i '' 's/None//g' ${D}/${county}_addresses.csv #> ${D}/${county}_addresses.csv

done
