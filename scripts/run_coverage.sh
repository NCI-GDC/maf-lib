#!/bin/bash

set -e

SCRIPTS_DIR=$(dirname $0);
ROOT_DIR=$(cd $SCRIPTS_DIR/.. && pwd -P)

# Simple usage function that is used to emit usage information when needed
usage() {
cat << EOF
Usage: $0 [options] 

OPTIONS:
   -c <coverage-tool>    The specific coverage executable to use (defaults to coverage2/3).
   -o <output-director>  The base output directory (default: coverage). 
EOF
}

COVERAGE_TOOLS=(coverage2 coverage3)
OUTPUT_DIR=${ROOT_DIR}/"coverage"

while getopts "c:o:h" OPTION; do
  case $OPTION in
    c) COVERAGE_TOOLS=($OPTARG);;
    o) OUTPUT_DIR=$OPTARG;;
    h) echo "Unknown option ${OPTION}"; usage; exit;;
    [?]) usage; exit;;
  esac
done

for TOOL in ${COVERAGE_TOOLS[@]}; do
  set +e
  TOOL_LOC=$(which $TOOL);
  set -e
  if [ "" == $TOOL_LOC ]; then
    echo "'$TOOL' not found" >&2;
    exit 1;
  fi
done

pushd $ROOT_DIR 2>&1 >/dev/null;
for TOOL in ${COVERAGE_TOOLS[@]}; do
  TOOL_NAME=$(basename $TOOL);
  TOOL_OUTPUT_DIR=${OUTPUT_DIR}/${TOOL_NAME};
  echo "Coverage for tool '$TOOL_NAME' will be written to '$TOOL_OUTPUT_DIR'";
  set +e
  $TOOL run -m unittest discover -s src
  set -e
  mkdir -p ${TOOL_OUTPUT_DIR};
  $TOOL report --include="src/*" --omit="src/*/tests/*,src/*/__init__.py"
  $TOOL html -d ${TOOL_OUTPUT_DIR} -i --include="src/*" --omit="src/*/tests/*,src/*/__init__.py"
done
popd
