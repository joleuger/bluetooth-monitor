#!/bin/sh

# login as audioclient using e.g. "machinectl shell --uid audioclient"
bluetoothctl

scan on
pairable on
pair A0:E9:DB:10:3F:B9
trust A0:E9:DB:10:3F:B9
exit

connect A0:E9:DB:10:3F:B9


bluez_sink.A0_E9_DB_10_3F_B9.a2dp_sink


gst-launch-1.0 -v playbin uri=http://192.168.50.221:8000/egofm.mp3 output="pulsesink device=bluez_sink.A0_E9_DB_10_3F_B9.a2dp_sink"
