#!/bin/bash
#
# run a program in a default venv - useful for python scripts in systemd
# edit the path below to point to your venv
@
VENV="$1"
shift
[[ -d "${VENV}" ]] && source "${VENV}/bin/activate"
exec $@
