#!/usr/bin/python3

# Copyright (c) 2017 Johannes Leupolz
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import asyncio, gbulb
from pydbus import SessionBus
import os
import yaml
import argparse
from core import BluetoothAudioBridge
import signal

parser = argparse.ArgumentParser()
parser.add_argument("--config", help="path configuration file (yaml format)")
args=parser.parse_args()


appConfigFilePath=None

if args.config:
  appConfigFilePath=args.config
elif os.getenv("XDG_CONFIG_HOME"):
  xdgConfigDir=os.getenv("XDG_CONFIG_HOME")
  appConfigDir=os.path.join(xdgConfigDir,"bluetooth-speaker-audio-bridge")
  if not os.path.exists(appConfigDir):
    os.makedirs(appConfigDir)
  appConfigFilePath=os.path.join(appConfigDir,"config.yaml")

appConfig={}
if not appConfigFilePath==None:
  print("Try to use configuration file "+appConfigFilePath)
  if os.path.isfile(appConfigFilePath):
    configFile=open(appConfigFilePath,"r")
    appConfig=yaml.load(configFile)
  else:
    print("Configuration file not found. Using default configuration")
else:
  print("Cannot locate path of configuration file. Need $XDG_CONFIG_HOME or custom path to configuration file as --config parameter.  Using default configuration")

if "traceLevel" not in  appConfig:
  appConfig["traceLevel"]=0
if "useMqtt" not in  appConfig:
  appConfig["useMqtt"]=False
if "updateConfig" not in appConfig:
  appConfig["updateConfig"]=False
if "bluetoothDevices" not in appConfig:
  appConfig["bluetoothDevices"]={}
for device,deviceConfig in appConfig["bluetoothDevices"].items():
  if "onConnectCommand" not in deviceConfig:
    deviceConfig["onConnectCommand"]=None
  if "onDisconnectCommand" not in deviceConfig:
    deviceConfig["onDisconnectCommand"]=None
print("trace level (higher means more output): "+str(appConfig["traceLevel"]))
print("use mqtt: "+str(appConfig["useMqtt"]))
print("update configuration file: "+str(appConfig["updateConfig"]))
for device,deviceConfig in appConfig["bluetoothDevices"].items():
  print("bluetooth device (must be in upper case form, e.g. A0_14_...): "+str(device))
  print("onConnectCommand: "+str(deviceConfig["onConnectCommand"]))
  print("onDisconnectCommand: "+str(deviceConfig["onDisconnectCommand"]))

def save_config():
  if (not appConfigFilePath==None) and appConfig["updateConfig"]:
    print("update settings file")
    configFile=open(appConfigFilePath,"w")
    yaml.dump(appConfig,configFile)


# create event loop
gbulb.install()
loop=asyncio.get_event_loop()

# create instance of bluetooth audio bridge main class
bluetoothAudioBridge=BluetoothAudioBridge(loop)
bluetoothAudioBridge.TraceLevel=appConfig["traceLevel"]
bluetoothAudioBridge.btDeviceConfig = appConfig["bluetoothDevices"]

#register termination handler
def ask_exit(signame):
    print("got signal %s: exit" % signame)
    #loop.run_until_complete(bluetoothAudioBridge.unregister())
    save_config()
    loop.stop()
    # everything after this point will not be reached
for signame in ('SIGINT', 'SIGTERM'):
    loop.add_signal_handler(getattr(signal, signame), lambda : ask_exit(signame))

#register dbus
loop.run_until_complete(bluetoothAudioBridge.registerDbus())
loop.run_forever()


# this point will never be reached
loop.close()
print("Finished") 
