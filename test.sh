#!/usr/bin/env bash
set -o errexit
set -o pipefail

start() { echo travis_fold':'start:$1; echo $1; }
end() { set +v; echo travis_fold':'end:$1; echo; echo; }
die() { set +v; echo "$*" 1>&2 ; exit 1; }

start flake8
flake8
end flake8

start doctest
python -m doctest python/*.py -o ELLIPSIS
end doctest

start endtoend
rm fake-files/output/* || mkdir fake-files/output
CI=true ./linnarsson-osmfish.sh
# CI to get it to run as test locally;
# Redundant on Travis, but doesn't hurt anything.
diff -r fake-files/output fake-files/output-expected/ -x .DS_Store | head -n100
end endtoend
