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

import asyncio
import os
import yaml

class BluetoothMonitorConfigManager:
    def __init__(self, loop):
        self.loop = loop
        self.trace = lambda level,msg: print(msg)
        self.appConfigFilePath = None
        self.lastTimeConfigOnDriveUpdated=-1
        self.appConfig={}
        self.Continue = True
        self.WatchingFuture=None
        self.onLoadConfigHandler = lambda appConfig: None


    def loadConfig(self):
      if not self.appConfigFilePath==None:
        print("Try to use configuration file "+self.appConfigFilePath)
        if os.path.isfile(self.appConfigFilePath):
          configFile=open(self.appConfigFilePath,"r")
          self.appConfig=yaml.load(configFile)
          self.updateLastTimeConfigOnDriveUpdated()
        else:
          print("Configuration file not found. Using default configuration")
      else:
        print("Cannot locate path of configuration file. Need $XDG_CONFIG_HOME or custom path to configuration file as --config parameter.  Using default configuration")
      
      if "traceLevel" not in self.appConfig:
        self.appConfig["traceLevel"]=0
      if "useMqtt" not in self.appConfig:
        self.appConfig["useMqtt"]=False
      if "updateConfig" not in self.appConfig:
        self.appConfig["updateConfig"]=False
      if "saveConfigOnExit" not in self.appConfig:
        self.appConfig["saveConfigOnExit"]=False
      if "bluetoothDevices" not in self.appConfig:
        self.appConfig["bluetoothDevices"]={}
      if "other_a2dp_sinks" not in self.appConfig["bluetoothDevices"]:
        self.appConfig["bluetoothDevices"]["other_a2dp_sinks"]={}
      for device,deviceConfig in self.appConfig["bluetoothDevices"].items():
        if "onConnectCommand" not in deviceConfig:
          deviceConfig["onConnectCommand"]=None
        if "onDisconnectCommand" not in deviceConfig:
          deviceConfig["onDisconnectCommand"]=None
      print("trace level (higher means more output): "+str(self.appConfig["traceLevel"]))
      print("use mqtt: "+str(self.appConfig["useMqtt"]))
      print("update configuration file: "+str(self.appConfig["updateConfig"]))
      print("save configuration file on exit: "+str(self.appConfig["saveConfigOnExit"]))
      for device,deviceConfig in self.appConfig["bluetoothDevices"].items():
        print("bluetooth device (must be in upper case form, e.g. A0_14_...): "+str(device))
        print("onConnectCommand: "+str(deviceConfig["onConnectCommand"]))
        print("onDisconnectCommand: "+str(deviceConfig["onDisconnectCommand"]))
      self.onLoadConfigHandler(self.appConfig)

    def updateLastTimeConfigOnDriveUpdated(self):
      if (not self.appConfigFilePath==None):
         self.lastTimeConfigOnDriveUpdated=os.stat(self.appConfigFilePath).st_mtime
      
    def checkIfConfigOnDriveWasUpdated(self):
      if (not self.appConfigFilePath==None):
         stamp=os.stat(self.appConfigFilePath).st_mtime
         if (stamp != self.lastTimeConfigOnDriveUpdated):
           self.updateLastTimeConfigOnDriveUpdated()
           return True
         else:
           return False
      return False
    
    def saveConfig(self):
      if (not self.appConfigFilePath==None):
        print("update settings file")
        configFile=open(appConfigFilePath,"w")
        yaml.dump(self.appConfig,configFile)

    async def watchConfig(self):
      if self.WatchingFuture != None:
         return
      self.WatchingFuture=self.loop.create_future()
      while self.Continue:
          self.trace(3,"checking for updated configuraton")
          if self.checkIfConfigOnDriveWasUpdated():
             self.loadConfig()
          await asyncio.sleep(1)
      self.WatchingFuture.set_result(True)
    
    async def startWatchConfig(self):
      asyncio.ensure_future(self.watchConfig())
      
    async def stopWatchConfig(self):
      self.Continue=False
      if (self.WatchingFuture):
          await self.WatchingFuture
      self.WatchingFuture = None

