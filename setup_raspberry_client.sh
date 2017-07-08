#!/bin/sh
apt-get update

apt-get -qy install pulseaudio gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-tools gstreamer1.0-pulseaudio gstreamer1.0-plugins-ugly
apt-get -qy install bluetooth bluez bluez-tools bluez-firmware pulseaudio-module-bluetooth
apt-get -qy install dbus-user-session
apt-get -qy install systemd-container

adduser --disabled-password --gecos "" audioclient
usermod -a -G bluetooth audioclient # see /etc/dbus-1/system.d/bluetooth.conf
usermod -a -G audio audioclient
udevadm control --reload
udevadm trigger

#enable dbus and pulseaudio for user
mkdir -p /home/audioclient/.config/systemd/user/sockets.target.wants
ln -s /usr/lib/systemd/user/dbus.socket /home/audioclient/.config/systemd/user/sockets.target.wants
ln -s /usr/lib/systemd/user/pulseaudio.socket /home/audioclient/.config/systemd/user/sockets.target.wants
mkdir -p /home/audioclient/.config/systemd/user/default.target.wants
ln -s /usr/lib/systemd/user/pulseaudio.service /home/audioclient/.config/systemd/user/default.target.wants/pulseaudio.service
chown -R audioclient:audioclient /home/audioclient/

# now we can use system
loginctl enable-linger audioclient
