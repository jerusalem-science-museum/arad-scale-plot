#!/bin/bash

#-> Make sure no other pi with the same name is on the network
HOSTNAME=pi22
PASSWORD=none
INSTALL_DIR=$HOME/Public/
CUR_USER=$(whoami)

#-> Make sure we don't run as root
if (( EUID == 0 )); then
   echo 'Please run without sudo!' 1>&2
   exit 1
fi

#-> Add common aliases
cat > $HOME/.bash_aliases <<EOF
alias sudo='sudo '
alias ll='ls -lhA'
alias ..='cd ..'
alias df='df -H'
alias du='du -ch'
alias read_cpu_temperature='/opt/vc/bin/vcgencmd measure_temp'
EOF

#-> Set passwords 'none' to current user and root user
echo -ne "$PASSWORD\n$PASSWORD\n" | sudo passwd $CUR_USER
echo -ne "$PASSWORD\n$PASSWORD\n" | sudo passwd root

#-> Set raspbian configs to match our hardware requirements
sudo sh -c 'cat >> /boot/config.txt <<EOF
max_usb_current=1
pi3-disable-bt
dtparam=audio=off
hdmi_force_hotplug=1
EOF'

#-> Remove unnecessary processes
sudo apt remove -y bluez bluez-firmware pi-bluetooth triggerhappy pigpio

#-> Update packags and install git, python and pip
sudo apt update
sudo apt install -y git python3 python3-pip python3-dev

#-> Update pip and install ipython and pyalsaaudio for audio control
sudo -H pip3 install --upgrade pip
sudo -H pip3 install --upgrade ipython

#-> Install pil and pygame, requires apt 'dev' packages
sudo apt install -y libsdl-dev libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsmpeg-dev libportmidi-dev libavformat-dev libswscale-dev python3-numpy
sudo -H pip3 install --upgrade Pillow pygame

#-> Create custom autostart
mkdir -p $HOME/.config/lxsession/LXDE-pi
cat > $HOME/.config/lxsession/LXDE-pi/autostart <<EOF
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
#@xscreensaver -no-splash
#@point-rpi
EOF

#-> Create install dir and clone repo into it
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR
git clone https://github.com/jerusalem-science-museum/scale_plot.git

#-> Install repo
$INSTALL_DIR/scale_plot/install.sh

#-> Install samba server for sharing 'Public' dir via network
sudo DEBIAN_FRONTEND=noninteractive apt install -y samba samba-common-bin
echo -ne '\n\n' | sudo smbpasswd -a $CUR_USER
sudo sh -c "cat >> /etc/samba/smb.conf <<EOF
force user = $CUR_USER
wins support = yes
[Public]
 comment = PiShare
 path = $HOME/Public
 browseable = Yes
 writeable = Yes
 guest ok = yes
 public = yes
 read only = no
 force user = $CUR_USER
EOF"

#-> Enable ssh, expand file system and set hostname
sudo raspi-config nonint do_ssh 0
sudo raspi-config nonint do_expand_rootfs
sudo raspi-config nonint do_hostname $HOSTNAME

#-> Reboot host for changes to take effect
echo 'Rebooting in 5 seconds...'
sleep 5; sudo reboot
