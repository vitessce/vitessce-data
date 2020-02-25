#!/usr/bin/env bash
set -o errexit
set -o pipefail

start() { echo travis_fold':'start:$1; echo $1; }
end() { set +v; echo travis_fold':'end:$1; echo; echo; }
die() { set +v; echo "$*" 1>&2 ; exit 1; }

if [ "$#" -ne 0 ]; then
    die 'No arguments: Lints the python files, and runs unit and end-to-end tests.'
fi

# start target
# TARGET=`sed -e 's/vitessce-data\///' cloud_target.txt`
# BRANCH=`git rev-parse --abbrev-ref HEAD`
# [[ "$BRANCH" == 'HEAD' ]] \
#   || [[ "$BRANCH" == "$TARGET" ]] \
#   || die "branch ($BRANCH) != target ($TARGET); Update target:
#           echo 'vitessce-data/$BRANCH' > cloud_target.txt"
# end target

# start flake8
# flake8 --exclude ./vips-8.7.1/
# end flake8
#
# start doctest
# python -m doctest python/*.py -o ELLIPSIS
# end doctest

start endtoend
rm -rf fake-files/output || echo 'Nothing to delete'
mkdir fake-files/output || echo 'Did not mkdir'
mkdir fake-files/output/linnarsson || echo 'Did not mkdir'

cp fake-files/output{-expected,}/linnarsson/linnarsson.neighborhoods.json
# Calculating neightborhoods is slow, and not a requirement right now,
# so copy over the expected output, and it will not be regenerated.

CI=true ./process.sh
# CI to get it to run as test locally;
# Redundant on Travis, but doesn't hurt anything.

diff -w -r fake-files/output fake-files/output-expected/ -x .DS_Store | head -n100 | cut -c 1-100
end endtoend
