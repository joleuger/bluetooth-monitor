Bluetooth monitor listens on D-Bus for connections of bluetooth devices.
It can be used to automatically start a online radio stream when a bluetooth speaker connects to the computer.

References used for the implementation
- https://github.com/tleyden/bluecast
- https://gist.github.com/boulund/8949499e17493e1c00db
- https://kofler.info/bluetooth-konfiguration-im-terminal-mit-bluetoothctl/
- https://stackoverflow.com/questions/34039588/asyncio-and-infinite-loop
- https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/adapter-api.txt
- https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/device-api.txt
- http://variwiki.com/index.php?title=BlueZ5_and_A2DP

# Note
Trust => Auto connect

# Tests

Run mosquitto in background when testing mqtt functionality

# Roadmap
- [X] Connecting to a MQTT-Server
- [ ] Example configuration for snapcast
- [ ] Auto-reload configurtion
- [ ] Remote control via MQTT
- [ ] Status reports via MQTT
- [ ] Switch to objectmanager InterfacesAdded and InterfacesRemoved feature
- [ ] Integrate small web server which allows pairing using a more comfortable interface
