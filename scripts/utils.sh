#!/usr/bin/env bash

die() { set +v; echo "$*" 1>&2 ; exit 1; }

add_arg() {
  # Helper for process_cells to build argument list.

  FILE_TYPE=$1
  DATA_TITLE=$2

  FILE="$OUTPUT/$DATA_TITLE.$FILE_TYPE.json"
  if [ -e "$FILE" ]
  then
    echo "$FILE_TYPE output already exists: $FILE"
  else
    CLI_ARGS="$CLI_ARGS --${FILE_TYPE}_file $FILE"
  fi
}
