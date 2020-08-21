#!/bin/bash

# DEST: dir where to uncompress raw data for analysis
# ORIG: dir with raw data stored as tar.bz2 archives split into n .tar.bz2.part<cc>
#DEST="wscaling1"
DEST="sscaling1"
ORIG="../../../rawdata/spatial_heterogeneity/$DEST"

# Create two txt files, each with a ordered list of session IDs
find $ORIG -maxdepth 1 -iname "rp.session.*.part.*" -type f | sed "s|$(sed 's/[\*\.&]/\\&/g' <<<$ORIG)/||" | sed 's|\.tar\.bz2\.part\...||' | sort -u > $ORIG/orig_sessions_list.txt
find $DEST -maxdepth 1 -iname "rp.session.*" -type d | sed "s|$(sed 's/[\*\.&]/\\&/g' <<<$DEST)/||" | sort -u > $DEST/dest_sessions_list.txt 

# Find the missing sessions IDs in ORIG and concatenate the missing data into tar.bz2 archives
for d in `comm -13 $DEST/dest_sessions_list.txt $ORIG/orig_sessions_list.txt`
do 
	cat $ORIG/$d.tar.bz2.part.* > $DEST/$d.tar.bz2
done

# Uncompressed the tar.bz2 archives
for f in `ls $DEST/*.tar.bz2`; do tar xfj $f -C $DEST; done

# Remove the archives.
rm $DEST/*.tar.bz2
