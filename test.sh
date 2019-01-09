set -o errexit

start() { echo travis_fold':'start:$1; echo $1; }
end() { set +v; echo travis_fold':'end:$1; echo; echo; }
die() { set +v; echo "$*" 1>&2 ; exit 1; }

start flake8
flake8
end flake8

start doctest
python -m doctest *.py
end doctest
