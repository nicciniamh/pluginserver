#!/bin/bash
#
# run a program in a default venv - useful for python scripts in systemd
# edit the path below to point to your venv
@
VENV=/home/user/venv # Edit me


[[ -d "${VENV}" ]] && source "${VENV}/nin/activate"
exec $@
