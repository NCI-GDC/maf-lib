#!/bin/bash

set -e

SCRIPTS_DIR=$(dirname $0);
ROOT_DIR=$(cd $SCRIPTS_DIR/.. && pwd -P)

COVERAGE=$1;
if [ "" == "${COVERAGE}" ]; then
    echo "Coverage version (ex. coverage2, coverage3) required" >&2;
    exit 1;
fi

pushd $ROOT_DIR 2>&1 >/dev/null;
set +e
$COVERAGE run -m unittest discover -s src
set -e
$COVERAGE report --include="src/*" --omit="src/*/tests/*,src/*/__init__.py"
$COVERAGE html -i --include="src/*" --omit="src/*/tests/*,src/*/__init__.py"
echo "Coverage reports can be found in ${ROOT_DIR}/htmlcov/index.html";
popd $ROOT_DIR 2>&1 >/dev/null;
