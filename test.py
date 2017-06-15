#!/usr/bin/python3

import asyncio, gbulb
from pydbus import SessionBus
import unittest
from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.broker import Broker
from pydbus.generic import signal

from core import BluetoothAudioBridge

startTheFakeBroker=False
mqttServerUrl="127.0.0.1:1883"

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
    def __init__(self):
        self.BridgeWorks = False
        self.broker = None

    @asyncio.coroutine
    def startFakeBroker(self):
        if startTheFakeBroker:
           print("Start fake broker")
           defaultMqtt = {}
           defaultMqtt["listeners"]={}
           defaultMqtt["listeners"]["default"]={"max-connections":5,"type":"tcp" }
           defaultMqtt["listeners"]["my-tcp-1"]={"bind":mqttServerUrl}
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
        print("connect MqttMessageEmitter")
        secondMqttClient=MQTTClient()
        connectionUrl="mqtt://"+mqttServerUrl
        await secondMqttClient.connect(connectionUrl)
        await secondMqttClient.publish('Broker/Test', b'Make Connection')
        await secondMqttClient.disconnect()
        print("connect message sent")

    async def startTestFakeDbusBluezObject(self):
        bus = SessionBus()
        bus.publish("BluetoothAudioBridge.FakeDbusObject", TestFakeDbusBluezObject())


class TestBridge(unittest.TestCase):
    def setUp(self):
        self.bus = SessionBus()
        gbulb.install()
        self.loop=asyncio.get_event_loop()
        self.fakes=TestFakeMethods()
        self.bluetoothAudioBridge=BluetoothAudioBridge(self.loop)
        self.bluetoothAudioBridge.DbusBluezPath = "BluetoothAudioBridge.FakeDbusObject"
        self.bluetoothAudioBridge.MqttServer = mqttServerUrl

    def test_connectToMqttTestBroker(self):
        self.loop.run_until_complete(self.fakes.startFakeBroker())
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerMqtt())
        self.loop.run_until_complete(self.fakes.sendMqttConnectMessage())
        self.loop.run_until_complete(asyncio.sleep(5))
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())
        self.loop.run_until_complete(self.fakes.stopFakeBroker())
        #self.assertTrue(self.fakes.BridgeWorks)

    def test_connectToDbus(self):
        self.loop.run_until_complete(self.fakes.startTestFakeDbusBluezObject())
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerDbus())
        self.loop.run_until_complete(asyncio.sleep(5))
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())
        #self.assertTrue(self.fakes.BridgeWorks)

    def todotest_listDbusEntriesOnIncomingMessage(self):
        self.loop.run_until_complete(self.fakes.startFakeBroker())
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerMqtt())
        self.loop.run_until_complete(asyncio.sleep(5))
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())
        self.loop.run_until_complete(self.fakes.stopFakeBroker())
        #self.assertTrue(self.fakes.BridgeWorks)
        


if __name__ == '__main__':
    unittest.main()

