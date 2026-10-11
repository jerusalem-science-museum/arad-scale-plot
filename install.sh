#!/bin/bash

#-> Make sure we don't run as root
if (( EUID == 0 )); then
	echo 'Please run without sudo!' 1>&2
	exit 1
fi

#-> Install python package
sudo apt install -y python3-tk python3-numpy

#-> Go to the directory of this script
cd "$(dirname "${BASH_SOURCE[0]}")"
SCALE_PLOT_DIR=$(pwd)

#-> Add to autostart
echo @$SCALE_PLOT_DIR/run_scale_plot.sh >> $HOME/.config/lxsession/LXDE-pi/autostart
