#!/usr/bin/python3

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
  if os.path.isfile(appConfigFilePath):
    configFile=file(appConfigFilePath,"r")
    appConfig=yaml.load(configFile)
  else:
    print("Configuration file not found. Using default configuration")
else:
  print("Cannot locate path of configuration file. Need $XDG_CONFIG_HOME or custom path to configuration file as --config parameter.  Using default configuration")

if "useMqtt" not in  appConfig:
  appConfig["useMqtt"]=False
if "updateConfig" not in appConfig:
  appConfig["updateConfig"]=False


if not appConfigFilePath==None:
  configFile=file(appConfigFilePath,"w")
  yaml.dump(appConfig,configFile)

#gbulb.install()
#asyncio.get_event_loop().run_forever()

def ask_exit(signame):
    print("got signal %s: exit" % signame)
    #loop.run_until_complete(bluetoothAudioBridge.unregister())
    loop.stop()

gbulb.install()
loop=asyncio.get_event_loop()
bluetoothAudioBridge=BluetoothAudioBridge(loop)

#register termination handler
for signame in ('SIGINT', 'SIGTERM'):
    loop.add_signal_handler(getattr(signal, signame), lambda : ask_exit(signame))

#register dbus
loop.run_until_complete(bluetoothAudioBridge.registerDbus())
loop.run_forever()
loop.close()
