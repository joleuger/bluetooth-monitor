#!/usr/bin/python3
import signal
import sys
import subprocess
import time
 
loopbackDevice=None

def signal_term_handler(signal, frame):
  print("Received SIGTERM. Close loopback")
  if loopbackDevice != None:
     subprocess.run(["/usr/bin/pactl", "unload-module", loopbackDevice])
  sys.exit(0)

signal.signal(signal.SIGTERM, signal_term_handler)

btmac=sys.argv[1]

print("bluetooth address to create loopback for: "+btmac)

createLoopbackProcess = subprocess.Popen(["/usr/bin/pactl", "load-module","module-loopback",'source="tobluetooth.monitor"','sink=bluez_sink.'+btmac+'.a2dp_sink'],stdout=subprocess.PIPE)
if createLoopbackProcess.returncode == 0:
  loopbackDevice=createLoopbackProcess.stdout.strip()

while True:
  time.sleep(10)

