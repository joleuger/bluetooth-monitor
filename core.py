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
from xml.etree import ElementTree
import subprocess
import os
import signal

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
            self.trace(0,"MQTT: received message")
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
            self.trace(0,msg.topic+" "+str(msg.payload))
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

    def btDeviceDetected(self,address):
        self.trace(0,"device detected "+address)

    def btDeviceRemoved(self,address):
        self.trace(0,"device removed "+address)

    def btDeviceConnected(self,address):
        self.trace(0,"device connected "+address)
        if address in self.btRunningProcesses:
            processGroupToKill=self.btRunningProcesses[address].pid
            os.killpg(os.getpgid(processGroupToKill), signal.SIGTERM)
            self.btRunningProcesses.pop(address,None)
        if address in self.btDeviceConfig:
           deviceConfig = self.btDeviceConfig[address]
           if "onConnectCommand" in deviceConfig:
              command=deviceConfig["onConnectCommand"]
              if command:
                commandToExecute=command.replace("$DEVICE",address)
                self.btRunningProcesses[address]=subprocess.Popen(commandToExecute,shell=True, preexec_fn=os.setsid)

    def btDeviceDisconnected(self,address):
        self.trace(0,"device disconnected "+address)
        if address in self.btRunningProcesses:
            processGroupToKill=self.btRunningProcesses[address].pid
            os.killpg(os.getpgid(processGroupToKill), signal.SIGTERM)
            self.btRunningProcesses.pop(address,None)
        if address in self.btDeviceConfig:
           deviceConfig = self.btDeviceConfig[address]
           if "onDisconnectCommand" in deviceConfig:
              command=deviceConfig["onDisconnectCommand"]
              if command:
                commandToExecute=command.replace("$DEVICE",address)
                self.btRunningProcesses[address]=subprocess.Popen(commandToExecute,shell=True, preexec_fn=os.setsid)

    async def lookForDbusChanges(self):
       while self.Continue:
           self.trace(3,"DBUS: wait for device")
           try:
               self.trace(0,"DBUS: connect to "+self.DbusBluezBusName+ " " +self.DbusBluezObjectPath)
               dbusNode = self.DbusBluezObject.get(self.DbusBluezBusName,self.DbusBluezObjectPath)
               dbusNodeXml = dbusNode.Introspect()
               xmlTree = ElementTree.fromstring(dbusNodeXml)
               # first check found <-> not found
               foundDevices = {}
               for child in xmlTree:
                   if child.tag=="node":
                       deviceNameWithPrefix = child.attrib['name']
                       deviceName = deviceNameWithPrefix[4:]
                       foundDevices[deviceName]=True
               removeDevices=[]
               for oldDevice in self.DbusBluezDiscoveredDevices:
                   if oldDevice not in foundDevices:
                       removeDevices.append(oldDevice)
                       self.dbusBtDeviceRemoved(oldDevice)
               for removeDevice in removeDevices:
                   self.DbusBluezDiscoveredDevices.pop(removeDevice,None)
               for foundDevice in foundDevices:
                   if foundDevice not in self.DbusBluezDiscoveredDevices:
                       self.DbusBluezDiscoveredDevices[foundDevice]=True
                       self.dbusBtDeviceDetected(foundDevice)
               # now check disconnect <-> connect
               connectedDevices = {}
               for foundDevice in foundDevices:
                   devicePath = self.DbusBluezObjectPath+ "/dev_"+foundDevice
                   deviceDbusNode = self.DbusBluezObject.get(self.DbusBluezBusName,devicePath)
                   isConnected = await self.loop.run_in_executor(None, lambda: deviceDbusNode.Connected)
                   if isConnected :
                      connectedDevices[foundDevice]=True
               disconnectedDevices=[]
               for alreadyConnectedDevice in self.DbusBluezConnectedDevices:
                   if alreadyConnectedDevice not in connectedDevices:
                      disconnectedDevices.append(alreadyConnectedDevice)
                      self.dbusBtDeviceDisconnected(alreadyConnectedDevice)
               for disconnectedDevice in disconnectedDevices:
                   self.DbusBluezConnectedDevices.pop(disconnectedDevice,None)
               for connectedDevice in connectedDevices:
                   if connectedDevice not in self.DbusBluezConnectedDevices:
                      self.DbusBluezConnectedDevices[connectedDevice]=True
                      self.dbusBtDeviceConnected(connectedDevice)
           #except KeyError:
           #    print("dbus error")
           except GError as err:
               self.trace(0,"dbus error")
               self.trace (0,err)
           await asyncio.sleep(1)
       print("finished looking for dbus changes")
       self.DbusBluezReceivingFuture.set_result(True)

    async def registerDbus(self):
        if self.DbusBluezOnSystemBus:
           self.DbusBluezObject = SystemBus()
        else:
           self.DbusBluezObject = SessionBus()
        self.trace(0,"listening on DBUS")
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

