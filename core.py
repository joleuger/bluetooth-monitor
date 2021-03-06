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

from pydbus import SessionBus
from pydbus import SystemBus
import asyncio, gbulb
from gi.repository.GLib import GError
#from hbmqtt.client import MQTTClient, ClientException
import paho.mqtt.client as mqtt
import subprocess
import os
import signal
import re

class BluetoothAudioBridge:
    def __init__(self, loop):
        self.loop = loop
        self.DbusPulseAudioPath=""
        self.DbusBluezOnSystemBus=True
        self.DbusBluezBusName="org.bluez"
        self.DbusBluezObjectPath="/org/bluez/hci0"
        self.DbusBluezObject=None
        self.DbusBluezReceivingFuture=None
        self.DbusBluezDiscoveredDevices={}
        self.DbusBluezUUIDsOfDevices={}
        self.DbusBluezConnectedDevices={}
        self.MqttPath="/BluetoothAudioBridge"
        self.MqttServer="localhost"
        self.MqttUsername="vhost:username"
        self.MqttPassword="password"
        self.MqttClient=None
        self.MqttMessageQueue=asyncio.Queue()
        self.MqttReceivingFuture=None
        self.Continue=True
        self.CancellationToken=self.loop.create_future()
        self.TraceLevel=0
        self.PollingCycle=3
        self.mqttReceivedConnect=self.makeConnect
        self.mqttReceivedPairAndTrust=self.makePairAndTrust
        self.mqttReceivedScan=self.makeScan
        self.dbusBtDeviceDetected=self.btDeviceDetected
        self.dbusBtDeviceRemoved=self.btDeviceRemoved
        self.dbusBtDeviceConnected=self.btDeviceConnected
        self.dbusBtDeviceDisconnected=self.btDeviceDisconnected
        self.dbusScanProcesses=0
        self.btDeviceConfig = {}
        self.btRunningProcesses = {}

    def loadConfig(self,appConfig):
        self.TraceLevel=appConfig["traceLevel"]
        self.PollingCycle=appConfig["pollingCycle"]
        self.btDeviceConfig = appConfig["bluetoothDevices"]

    def trace(self,level,msg):
        if self.TraceLevel >= level:
           print(msg)

    async def awaitOrStop(self,future):
        # currently unused
        done,pending = await asyncio.wait([self.CancellationToken, future],return_when=asyncio.FIRST_COMPLETED)
        firstFinished=next(iter(done))
        if firstFinished==self.CancellationToken:
            #Note: pending tasks are still running
            return (False,None)
        #print(firstFinished)
        #print(firstFinished.result())
        return (True,firstFinished.result())

    def makeConnect(self,message):
        self.trace(0,"MQTT: received connect")
        

    def makePairAndTrust(self,message):
        self.trace(0,"MQTT: received pair and trust")

    def makeScan(self,message):
        self.scanProcesses=self.scanProcesses+1
        self.trace(0,"MQTT: received scan")
        asyncio.ensure_future(self.stopScanningIn30Seconds)

    async def stopScanningIn30Seconds(self):
        await asyncio.sleep(30)
        self.scanProcesses=self.scanProcesses-1
        if (self.scanProcesses==0):
            self.trace(2,"stop scanning for devices")

    async def mqttProcessMessages(self):
        while self.Continue:
            message=await self.MqttMessageQueue.get()
            if message==None:
                self.trace(0,"stopping message proccessing")
                return
            self.trace(1,"MQTT: received message")
            if message.startswith("Connect"):
                self.mqttReceivedConnect(message)
            if message.startswith("Pair and trust"):
                self.mqttReceivedConnect(message)
            if message.startswith("Scan"):
                self.mqttReceivedScan(message)

    async def registerMqtt(self):
        def on_connect(client, userdata, flags, rc):
            self.trace(0,"Connected with result code "+str(rc))
            # Subscribing in on_connect() means that if we lose the connection and
            # reconnect then subscriptions will be renewed.
            client.subscribe("/BluetoothAudioBridge/commands")
        def on_message(client, userdata, msg):
            self.trace(1,msg.topic+" "+str(msg.payload))
            msgDecoded=msg.payload.decode("utf-8")
            asyncio.ensure_future(self.MqttMessageQueue.put(msgDecoded))
        async def mqttReceiving():
            while self.Continue:
                self.trace(3,"MQTT: wait for message")
                client.loop_read()
                client.loop_write()
                client.loop_misc()
                await asyncio.sleep(0.1)
            client.disconnect()
            client.loop_read()
            client.loop_write()
            client.loop_misc()
            self.MqttReceivingFuture.set_result(True)
            asyncio.ensure_future(self.MqttMessageQueue.put(None)) # add final (empty) message into queue for a clean shutdown
        def on_disconnect(client, userdata, rc):
            if rc != 0:
                self.trace(0,"Unexpected disconnection.")
        client = mqtt.Client(client_id="thing-bluetoothbridge",)
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        client.username_pw_set(self.MqttUsername, password=self.MqttPassword)
        client.connect(self.MqttServer, 1883, 60)
        #register receiver
        self.MqttReceivingFuture=self.loop.create_future()
        asyncio.ensure_future(self.mqttProcessMessages())
        asyncio.ensure_future(mqttReceiving())
        self.trace(0,"registered on MQTT")

    async def btDeviceDetected(self,address):
        self.trace(0,"device detected "+address)

    async def btDeviceRemoved(self,address):
        self.trace(0,"device removed "+address)

    def btClassIsAudio(self,btClass):
        # https://www.bluetooth.com/specifications/assigned-numbers/baseband
        major_service_audio_bit = 1<<21
        major_device_audio_bit = 1<<10
        is_audio_service = (major_service_audio_bit & btClass)==major_service_audio_bit
        is_audio_device = (major_device_audio_bit & btClass)==major_device_audio_bit
        return is_audio_service and is_audio_device

    def btDeviceHasA2DPSink(self,uuids):
        # https://github.com/pauloborges/bluez/blob/master/lib/uuid.h
        if "0000110b-0000-1000-8000-00805f9b34fb" in uuids:
            return True
        return False

    def stdoutOfPopen(self):
        if self.TraceLevel < 3:
           return subprocess.DEVNULL
        return None

    async def btDeviceConnected(self,address):
        self.trace(0,"device connected "+address)
        if address in self.btRunningProcesses:
            processGroupToKill=self.btRunningProcesses[address].pid
            os.killpg(os.getpgid(processGroupToKill), signal.SIGTERM)
            await asyncio.sleep(1)
            os.killpg(os.getpgid(processGroupToKill), signal.SIGKILL)
            self.btRunningProcesses.pop(address,None)
        deviceConfig=None
        if address in self.btDeviceConfig:
           deviceConfig = self.btDeviceConfig[address]
        else:
           uuids=self.DbusBluezUUIDsOfDevices[address]
           if self.btDeviceHasA2DPSink(uuids) and "other_a2dp_sinks" in self.btDeviceConfig:
              deviceConfig=self.btDeviceConfig["other_a2dp_sinks"]
        if deviceConfig!=None:
           if "onConnectCommand" in deviceConfig:
              command=deviceConfig["onConnectCommand"]
              if command:
                commandToExecute=command.replace("$DEVICE",address)
                self.btRunningProcesses[address]=subprocess.Popen(commandToExecute,shell=True, start_new_session=True,stdout=self.stdoutOfPopen(),stderr=self.stdoutOfPopen())

    async def btDeviceDisconnected(self,address):
        self.trace(0,"device disconnected "+address)
        if address in self.btRunningProcesses:
            processGroupToKill=self.btRunningProcesses[address].pid
            os.killpg(os.getpgid(processGroupToKill), signal.SIGTERM)
            await asyncio.sleep(1)
            os.killpg(os.getpgid(processGroupToKill), signal.SIGKILL)
            self.btRunningProcesses.pop(address,None)
        deviceConfig=None
        if address in self.btDeviceConfig:
           deviceConfig = self.btDeviceConfig[address]
        else:
           uuids=self.DbusBluezUUIDsOfDevices[address]
           if self.btDeviceHasA2DPSink(uuids) and "other_a2dp_sinks" in self.btDeviceConfig:
              deviceConfig=self.btDeviceConfig["other_a2dp_sinks"]
        if deviceConfig!=None:
           if "onDisconnectCommand" in deviceConfig:
              command=deviceConfig["onDisconnectCommand"]
              if command:
                commandToExecute=command.replace("$DEVICE",address)
                self.btRunningProcesses[address]=subprocess.Popen(commandToExecute,shell=True, start_new_session=True,stdout=self.stdoutOfPopen(),stderr=self.stdoutOfPopen())

    async def lookForDbusChanges(self):
       deviceFilter = re.compile("^[/]\w+[/]\w+[/]\w+[/]dev_(?P<btmac>\w+)$")
       while self.Continue:
           self.trace(3,"DBUS: wait for device")
           try:
               self.trace(1,"DBUS: GetManagedObjects()")
               managedObjects = await self.loop.run_in_executor(None, lambda: self.DbusBluezRootNode.GetManagedObjects())
               await asyncio.sleep(0.5)  # give PulseAudio a chance of connecting (not sure if necessary)
               foundDevices={}
               for objPath,obj in managedObjects.items():
                  match = deviceFilter.match(objPath)
                  if match:
                     btmac=match.group("btmac")
                     dev=obj[self.DbusBluezBusName+".Device1"]
                     foundDevices[btmac]=dev
               self.trace(3,"Found "+str(len(foundDevices))+" devices")

               removeDevices=[]
               for oldDevice in self.DbusBluezDiscoveredDevices:
                   if oldDevice not in foundDevices:
                       removeDevices.append(oldDevice)
                       await self.dbusBtDeviceRemoved(oldDevice)
               for removeDevice in removeDevices:
                   self.DbusBluezDiscoveredDevices.pop(removeDevice,None)
               for foundDevice in foundDevices:
                   if foundDevice not in self.DbusBluezDiscoveredDevices:
                       self.DbusBluezDiscoveredDevices[foundDevice]=True
                       await self.dbusBtDeviceDetected(foundDevice)
               # now check disconnect <-> connect
               connectedDevices = {}
               for foundDevice,dev in foundDevices.items():
                   if foundDevice not in self.DbusBluezUUIDsOfDevices:
                       self.DbusBluezUUIDsOfDevices[foundDevice] = dev["UUIDs"]
                   isConnected = dev["Connected"] 
                   if isConnected :
                      connectedDevices[foundDevice]=True
               disconnectedDevices=[]
               for alreadyConnectedDevice in self.DbusBluezConnectedDevices:
                   if alreadyConnectedDevice not in connectedDevices:
                      disconnectedDevices.append(alreadyConnectedDevice)
                      await self.dbusBtDeviceDisconnected(alreadyConnectedDevice)
               for disconnectedDevice in disconnectedDevices:
                   self.DbusBluezConnectedDevices.pop(disconnectedDevice,None)
               for connectedDevice in connectedDevices:
                   if connectedDevice not in self.DbusBluezConnectedDevices:
                      self.DbusBluezConnectedDevices[connectedDevice]=True
                      await self.dbusBtDeviceConnected(connectedDevice)
           except KeyError as err:
               self.trace(0,"dbus error (KeyError)")
               print(err)
               self.trace(0,err)
           except GError as err:
               self.trace(0,"dbus error (GError)")
               self.trace (0,err)
           await asyncio.sleep(self.PollingCycle)
       print("finished looking for dbus changes")
       self.DbusBluezReceivingFuture.set_result(True)

    async def registerDbus(self):
        try:
           if self.DbusBluezOnSystemBus:
              self.DbusBluezObject = SystemBus()
           else:
              self.DbusBluezObject = SessionBus()
           self.trace(0,"listening on D-BUS")
           self.DbusBluezRootNode = self.DbusBluezObject.get(self.DbusBluezBusName,"/")
           self.trace(0,"connected to org.bluez")
        except GError as err:
           self.trace(0,"dbus error (register)")
           self.trace (0,err)
           self.DbusBluezRootNode=None
        if self.DbusBluezRootNode:
           self.DbusBluezReceivingFuture=self.loop.create_future()
           asyncio.ensure_future(self.lookForDbusChanges())
        

    async def register(self):
        await self.registerMqtt()
        await self.registerDbus()

    async def unregister(self):
        self.Continue=False
        if (self.DbusBluezReceivingFuture):
            await self.DbusBluezReceivingFuture
        self.DbusBluezReceivingFuture = None
        if (self.MqttReceivingFuture):
            await self.MqttReceivingFuture
        self.MqttReceivingFuture=None

