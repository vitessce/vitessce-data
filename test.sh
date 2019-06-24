#!/usr/bin/env bash
set -o errexit
set -o pipefail

start() { echo travis_fold':'start:$1; echo $1; }
end() { set +v; echo travis_fold':'end:$1; echo; echo; }
die() { set +v; echo "$*" 1>&2 ; exit 1; }

if [ "$#" -ne 0 ]; then
    die 'No arguments: Lints the python files, and runs unit and end-to-end tests.'
fi

start flake8
flake8
end flake8

start doctest
python -m doctest python/*.py -o ELLIPSIS
end doctest

start endtoend
rm -rf fake-files/output || echo 'Nothing to delete'
mkdir fake-files/output || echo 'Did not mkdir'

cp fake-files/output{-expected,}/linnarsson.neighborhoods.json
# Calculating neightborhoods is slow, and not a requirement right now,
# so copy over the expected output, and it will not be regenerated.

CI=true ./linnarsson-osmfish.sh
# CI to get it to run as test locally;
# Redundant on Travis, but doesn't hurt anything.

perl -pine \
  's/uuid:.{36}/uuid:00000000-0000-0000-0000-000000000000/;
	s/<AcquisitionDate>.{26}/<AcquisitionDate>0000-00-00T00:00:00.000000/;
	s/tifffile.py.{20}/tifffile.py.0000:00:00 00:00:00/' fake-files/output/linnarsson.images.ome.tif

# If you have problems with the TIFF, try this:
#
# hexdump -C fake-files/output/linnarsson.images.ome.tif > output-dump.txt
# hexdump -C fake-files/output-expected/linnarsson.images.ome.tif > output-expected-dump.txt
# diff -y output-dump.txt output-expected-dump.txt

diff -w -r fake-files/output fake-files/output-expected/ -x .DS_Store | head -n100 | cut -c 1-100
end endtoend
