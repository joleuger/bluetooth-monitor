#!/bin/sh
apt-get update

apt-get -qy install pulseaudio gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-tools gstreamer1.0-pulseaudio gstreamer1.0-plugins-ugly
apt-get -qy install bluetooth bluez bluez-tools bluez-firmware pulseaudio-module-bluetooth
apt-get -qy install dbus-user-session
apt-get -qy install systemd-container
apt-get -qy install python3-pip python3-yaml

pip3 install pydbus
pip3 install gbulb
pip3 install paho-mqtt
#pip3 install hbmqtt

adduser --disabled-password --gecos "" audioclient
usermod -a -G bluetooth audioclient # see /etc/dbus-1/system.d/bluetooth.conf
usermod -a -G audio audioclient
udevadm control --reload
udevadm trigger

#copy script into user directory
mkdir -p /home/audioclient/bluetooth-monitor
cp * -Rf /home/audioclient/bluetooth-monitor
cp /home/audioclient/bluetooth-monitor/example-config.yaml /home/audioclient/bluetooth-monitor/config.yaml
chown -R audioclient:audioclient /home/audioclient/

#enable dbus and pulseaudio for user
mkdir -p /home/audioclient/.config/systemd/user/sockets.target.wants
ln -s /usr/lib/systemd/user/dbus.socket /home/audioclient/.config/systemd/user/sockets.target.wants
ln -s /usr/lib/systemd/user/pulseaudio.socket /home/audioclient/.config/systemd/user/sockets.target.wants
mkdir -p /home/audioclient/.config/systemd/user/default.target.wants
ln -s /usr/lib/systemd/user/pulseaudio.service /home/audioclient/.config/systemd/user/default.target.wants/pulseaudio.service
cp contrib/bluetooth-monitor.service /home/audioclient/.config/systemd/user
cp contrib/pulseaudio-audioclient.service /home/audioclient/.config/systemd/user
#ln -s /home/audioclient/.config/systemd/user/pulseaudio-audioclient.service /home/audioclient/.config/systemd/user/default.target.wants/pulseaudio-audioclient.service
#ln -s /home/audioclient/.config/systemd/user/bluetooth-monitor.service /home/audioclient/.config/systemd/user/default.target.wants/bluetooth-monitor.service
chown -R audioclient:audioclient /home/audioclient/

# now we can use system
loginctl enable-linger audioclient

# you can login with user audioclient with
#    > machinectl shell --uid audioclient"
# then, you can enable bluetooth monitor
#    > systemctl --user enable --now bluetooth-monitor
# when you change the configuration, do not forget to
#    > systemctl --user restart bluetooth-monitor
