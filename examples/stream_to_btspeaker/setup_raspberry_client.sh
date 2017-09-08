#!/bin/sh
apt-get update

apt-get -qy install pulseaudio gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-tools gstreamer1.0-pulseaudio gstreamer1.0-plugins-ugly gstreamer1.0-libav
apt-get -qy install bluetooth bluez bluez-tools bluez-firmware pulseaudio-module-bluetooth
apt-get -qy install dbus-user-session
apt-get -qy install systemd-container
apt-get -qy install wget

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
cp ../../core.py ../../main.py ../../configManager.py ../../pulseaudio-create-loopback.py -f /home/audioclient/bluetooth-monitor
cp ../../example-config.yaml /home/audioclient/bluetooth-monitor/config.yaml
chown -R audioclient:audioclient /home/audioclient/


mkdir -p /home/audioclient/.config/systemd/user/sockets.target.wants
mkdir -p /home/audioclient/.config/systemd/user/default.target.wants

# enable dbus for user
# ln -s /usr/lib/systemd/user/dbus.socket /home/audioclient/.config/systemd/user/sockets.target.wants # should not be necessary with package dbus-user-session installed

# enable pulseaudio
ln -s /usr/lib/systemd/user/pulseaudio.socket /home/audioclient/.config/systemd/user/sockets.target.wants
ln -s /usr/lib/systemd/user/pulseaudio.service /home/audioclient/.config/systemd/user/default.target.wants/pulseaudio.service
# ensure, that pulseaudio always restarts
mkdir -p /home/audioclient/.config/systemd/user/pulseaudio.service.d
cp pulseaudio-restart.conf /home/audioclient/.config/systemd/user/pulseaudio.service.d
# cp pulseaudio-custom.conf /home/audioclient/.config/systemd/user/pulseaudio.service.d
# you can check the used settings with "systemctl --user show pulseaudio.service" when logged in as audioclient
mkdir -p /home/audioclient/.config/pulse
cp /etc/pulse/daemon.conf /home/audioclient/.config/pulse/daemon.conf
echo "allow-exit = no" >> /home/audioclient/.config/pulse/daemon.conf
echo "exit-idle-time = -1" >> /home/audioclient/.config/pulse/daemon.conf
cp etc_security_limits_d_audioclient.conf /etc/security/limits.d/



# enable virtual pulse device "snapcast". enable bridge from alsa to pulse. install snapcast
#cp /etc/pulse/default.pa /home/audioclient/.config/pulse/default.pa
#echo load-module module-null-sink rate=44100 channels=2 sink_name=snapcast >> /home/audioclient/.config/pulse/default.pa
#apt-get install -qy libasound2-plugins
#cp home_audioclient_.asoundrc /home/audioclient/.asoundrc

#build snapclient
#apt-get install -qy libasound2-dev libvorbisidec-dev libvorbis-dev libflac-dev alsa-utils libavahi-client-dev avahi-daemon
#mkdir -p /build
#cd /build
#git clone https://github.com/badaix/snapcast.git
#cd snapcast
#git checkout tags/v0.11.1
#cd externals
#git submodule update --init --recursive
#cd ../client
#make
#cp snapclient /usr/local/bin

#alternative: download precompiled snapclient
#mkdir -p /tmp/snapclient
#cd /tmp/snapclient
#wget https://github.com/badaix/snapcast/releases/download/v0.11.1/snapclient_0.11.1_armhf.deb
#dpkg -x snapclient_0.11.1_armhf.deb .
#cp ./usr/bin/snapclient /usr/local/bin/snapclient
#cd /
#rm -rf /tmp/snapclient

#enable snapclient user systemd service
#cp snapclient.service /home/audioclient/.config/systemd/user
#ln -s /home/audioclient/.config/systemd/user/snapclient.service /home/audioclient/.config/systemd/user/default.target.wants/snapclient.service



# enable bluetooth-monitor
cp bluetooth-monitor.service /home/audioclient/.config/systemd/user
ln -s /home/audioclient/.config/systemd/user/bluetooth-monitor.service /home/audioclient/.config/systemd/user/default.target.wants/bluetooth-monitor.service

# fix file permissions
chown -R audioclient:audioclient /home/audioclient/


# now we can use system
loginctl enable-linger audioclient

# you can login with user audioclient with
#    > machinectl shell --uid audioclient"
# then, you can enable bluetooth monitor
#    > systemctl --user enable --now bluetooth-monitor
# when you change the configuration, do not forget to
#    > systemctl --user restart bluetooth-monitor
