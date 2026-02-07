#!/bin/sh

THIS_DIR="$(readlink -f $(dirname $0))"
NAME="$(basename $0 .sh)"

export PATH=$PATH:/mnt/SDCARD/System/bin
export PYSDL2_DLL_PATH=/usr/lib

export PYTHONPATH=/root/.local/lib/python3.10/site-packages:/mnt/SDCARD/System/lib/python3.11:/mnt/SDCARD/Apps/PortMaster/PortMaster/exlibs:/mnt/SDCARD/System/lib/python3.11/site-packages:$PYTHONPATH

export SDL_VIDEODRIVER=mali
export SDL_RENDER_DRIVER=opengles2

python3 -m maxbloks.terminal.main &> /tmp/terminal.log
