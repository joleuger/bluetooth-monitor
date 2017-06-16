#!/usr/bin/python3

import asyncio, gbulb
from pydbus import SessionBus
import unittest
from hbmqtt.broker import Broker
from pydbus.generic import signal
import paho.mqtt.publish as mqttpublish

from core import BluetoothAudioBridge

startTheFakeBroker=False
mqttServer="127.0.0.1"
mqttUsername="username"
mqttPassword="pw"

class TestFakeDbusBluezObject():
    dbus="""
       <node>
         <interface name='BluetoothAudioBridge.FakeDbusBluezObject'>
           <method name='EchoString'>
             <arg type='s' name='a' direction='in'/>
             <arg type='s' name='response' direction='out'/>
           </method>
           <method name='OutputAnything'>
             <arg type='s' name='response' direction='out'/>
           </method>
           <property name="SomeProperty" type="s" access="readwrite">
             <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
           </property>
         </interface>
       </node>"""

    def EchoString(self, s):
        """returns whatever is passed to it"""
        return s

    def OutputAnything(self):
        """returns something"""
        return "something"

    def __init__(self):
        self._someProperty = "initial value"
  
    @property
    def SomeProperty(self):
        return self._someProperty
  
    @SomeProperty.setter
    def SomeProperty(self, value):
        self._someProperty = value
        self.PropertiesChanged("BluetoothAudioBridge.FakeDbusBluezObject", {"SomeProperty": self.SomeProperty}, [])
  
    PropertiesChanged = signal()


class TestFakeMethods():
    def __init__(self,bluetoothAudioBridge):
        self.BridgeWorks = False
        self.TestResult = False
        self.broker = None
        self.bluetoothAudioBridge=bluetoothAudioBridge
        self.bluetoothAudioBridge.DbusBluezPath = "BluetoothAudioBridge.FakeDbusObject"
        self.bluetoothAudioBridge.MqttServer = mqttServer
        self.bluetoothAudioBridge.MqttUsername = mqttUsername
        self.bluetoothAudioBridge.MqttPassword = mqttPassword

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

    async def sendMqttConnectMessage(self):
        mqttpublish.single("/BluetoothAudioBridge", payload="Make Connection", hostname=mqttServer
, port=1883, auth = {'username':mqttUsername, 'password':mqttPassword})
        print("connect message sent")

    async def startTestFakeDbusBluezObject(self):
        bus = SessionBus()
        bus.publish("BluetoothAudioBridge.FakeDbusObject", TestFakeDbusBluezObject())

    async def cancelIn2Seconds(self):
        await asyncio.sleep(2)
        self.bluetoothAudioBridge.CancellationToken.set_result(True)

    async def setResultInXSecondsCancelable(self,time):
        (finished,result) = await self.bluetoothAudioBridge.awaitOrStop(asyncio.sleep(time))
        if finished:
            print("set Result to true")
            self.TestResult=True

class TestBridge(unittest.TestCase):
    def setUp(self):
        self.bus = SessionBus()
        gbulb.install()
        self.loop=asyncio.get_event_loop()
        self.bluetoothAudioBridge=BluetoothAudioBridge(self.loop)
        self.fakes=TestFakeMethods(self.bluetoothAudioBridge)

    def atest_connectToMqttTestBroker(self):
        self.loop.run_until_complete(self.fakes.startFakeBroker())
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerMqtt())
        self.loop.run_until_complete(asyncio.sleep(1)) #must wait for a succesful connection
        self.loop.run_until_complete(self.fakes.sendMqttConnectMessage())
        self.loop.run_until_complete(asyncio.sleep(2))
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())
        self.loop.run_until_complete(self.fakes.stopFakeBroker())
        #self.assertTrue(self.fakes.BridgeWorks)

    def atest_connectToDbus(self):
        self.loop.run_until_complete(self.fakes.startTestFakeDbusBluezObject())
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerDbus())
        self.loop.run_until_complete(asyncio.sleep(2))
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())
        #self.assertTrue(self.fakes.BridgeWorks)

    def todotest_listDbusEntriesOnIncomingMessage(self):
        self.loop.run_until_complete(self.fakes.startFakeBroker())
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerMqtt())
        self.loop.run_until_complete(asyncio.sleep(2))
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())
        self.loop.run_until_complete(self.fakes.stopFakeBroker())
        #self.assertTrue(self.fakes.BridgeWorks)
        
    def test_awaitOrStop1(self):
        asyncio.ensure_future(self.fakes.cancelIn2Seconds())
        asyncio.ensure_future(self.fakes.setResultInXSecondsCancelable(3))
        self.loop.run_until_complete(asyncio.sleep(4))
        self.assertFalse(self.fakes.TestResult)

    def test_awaitOrStop2(self):
        asyncio.ensure_future(self.fakes.cancelIn2Seconds())
        asyncio.ensure_future(self.fakes.setResultInXSecondsCancelable(1))
        self.loop.run_until_complete(asyncio.sleep(4))
        self.assertTrue(self.fakes.TestResult)

if __name__ == '__main__':
    unittest.main()

