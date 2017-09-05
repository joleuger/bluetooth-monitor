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
import unittest
from hbmqtt.broker import Broker
from pydbus.generic import signal
import paho.mqtt.publish as mqttpublish

from core import BluetoothAudioBridge

startTheFakeBroker=False
mqttServer="127.0.0.1"
mqttUsername="username"
mqttPassword="pw"


class TestFakeMethods():
    def __init__(self,bluetoothAudioBridge):
        self.TestResult = 0
        self.broker = None
        self.bluetoothAudioBridge=bluetoothAudioBridge
        self.bluetoothAudioBridge.DbusBluezBusName = "BluetoothAudioBridge.FakeDbusObject"
        self.bluetoothAudioBridge.DbusBluezObjectPath = "/BluetoothAudioBridge/FakeDbusObject/hci0"
        self.bluetoothAudioBridge.MqttServer = mqttServer
        self.bluetoothAudioBridge.MqttUsername = mqttUsername
        self.bluetoothAudioBridge.MqttPassword = mqttPassword
        self.bluetoothAudioBridge.DbusBluezOnSystemBus=False

    @asyncio.coroutine
    def startFakeBroker(self):
        if startTheFakeBroker:
           print("Start fake broker")
           defaultMqtt = {}
           defaultMqtt["listeners"]={}
           defaultMqtt["listeners"]["default"]={"max-connections":5,"type":"tcp" }
           defaultMqtt["listeners"]["my-tcp-1"]={"bind":mqttServer}
           defaultMqtt["timeout-disconnect-delay"]=2
           defaultMqtt["auth"]={}
           defaultMqtt["auth"]["plugins"]=["auth.anonymous"]
           defaultMqtt["auth"]["allow-anonymous"]=True
           defaultMqtt["auth"]["password-file"]=None
           self.broker = Broker(defaultMqtt)
           try:
               yield from self.broker.start()
           except Exception:
               #workaround
               pass

    @asyncio.coroutine
    def stopFakeBroker(self):
        if startTheFakeBroker:
           print("shutdown fake broker")
           yield from self.broker.shutdown()

    def callerWithOneParameterWasCalled(self):
        def methodCall(parameter):
           print("parameter "+parameter)
           self.TestResult=self.TestResult+1
        return methodCall

    def callerWithOneParameterWasCalledAsync(self):
        async def methodCall(parameter):
           print("parameter "+parameter)
           self.TestResult=self.TestResult+1
        return methodCall

    async def sendMqttConnectMessage(self):
        mqttpublish.single("/BluetoothAudioBridge/commands", payload="Connect: ", hostname=mqttServer
, port=1883, auth = {'username':mqttUsername, 'password':mqttPassword})
        print("connect message sent")

    async def sendMqttPairAndTrustMessage(self):
        mqttpublish.single("/BluetoothAudioBridge/commands", payload="Pair and trust: ", hostname=mqttServer
, port=1883, auth = {'username':mqttUsername, 'password':mqttPassword})
        print("pair and trust message sent")

    async def sendMqttScanMessage(self):
        mqttpublish.single("/BluetoothAudioBridge/commands", payload="Scan:", hostname=mqttServer
, port=1883, auth = {'username':mqttUsername, 'password':mqttPassword})
        print("scan message sent")

    async def cancelIn2Seconds(self):
        await asyncio.sleep(2)
        self.bluetoothAudioBridge.CancellationToken.set_result(True)

    async def setResultInXSecondsCancelable(self,time):
        (finished,result) = await self.bluetoothAudioBridge.awaitOrStop(asyncio.sleep(time))
        if finished:
            print("set Result to true")
            self.TestResult=1



class TestBridge(unittest.TestCase):
    def setUp(self):
        gbulb.install()
        self.loop=asyncio.get_event_loop()
        self.bluetoothAudioBridge=BluetoothAudioBridge(self.loop)
        self.fakes=TestFakeMethods(self.bluetoothAudioBridge)

    def atest_scanMessageSendToTestBrokerIsReceived(self):
        self.bluetoothAudioBridge.mqttReceivedScan=self.fakes.callerWithOneParameterWasCalled()
        self.loop.run_until_complete(self.fakes.startFakeBroker())
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerMqtt())
        self.loop.run_until_complete(asyncio.sleep(1)) #must wait for a succesful connection
        self.loop.run_until_complete(self.fakes.sendMqttScanMessage())
        self.loop.run_until_complete(asyncio.sleep(2))
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())
        self.loop.run_until_complete(self.fakes.stopFakeBroker())
        self.assertEqual(self.fakes.TestResult,1)

    def atest_listMockedDbusEntriesOnScanMessage(self):
        self.loop.run_until_complete(self.fakes.startFakeBroker())
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerMqtt())
        self.loop.run_until_complete(asyncio.sleep(2))
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())
        self.loop.run_until_complete(self.fakes.stopFakeBroker())
        #self.assertTrue(self.fakes.BridgeWorks)
        
    def atest_awaitOrStop1(self):
        asyncio.ensure_future(self.fakes.cancelIn2Seconds())
        asyncio.ensure_future(self.fakes.setResultInXSecondsCancelable(3))
        self.loop.run_until_complete(asyncio.sleep(4))
        self.assertEqual(self.fakes.TestResult,0)

    def atest_awaitOrStop2(self):
        asyncio.ensure_future(self.fakes.cancelIn2Seconds())
        asyncio.ensure_future(self.fakes.setResultInXSecondsCancelable(1))
        self.loop.run_until_complete(asyncio.sleep(4))
        self.assertEqual(self.fakes.TestResult,1)

if __name__ == '__main__':
    unittest.main()

