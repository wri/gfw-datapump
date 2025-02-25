#!/bin/bash

# This does a hash of the zip file, but that includes all the modified times of the
# files, which keep changing, even when the file names and contents are the same. I
# tried generating a hash using only filenames and contents, but terraform seems to
# create its own hash of the layer.zip file as well, so basically we're always going
# to update the layer.zip no matter what, which seems fine.
hash=$(sha256sum $1 | cut -d' ' -f1)

echo '{ "hash": "'"$hash"'" }'
