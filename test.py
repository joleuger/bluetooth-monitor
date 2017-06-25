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

class TestFakeDbusBluezAdapter():
    dbus="""
       <node>
         <interface name='BluetoothAudioBridge.FakeDbusBluezObject.Adapter1'>
           <method name='StartDiscovery'>
           </method>
           <method name='StopDiscovery'>
           </method>
           <property name="Address" type="s" access="read">
           </property>
         </interface>
       </node>"""

    def StartDiscovery(self):
        """start discovery"""
        print("startDiscovery")
        self.fakes.TestResult=self.fakes.TestResult+1

    def StopDiscovery(self):
        """stop discovery"""
        print("stopDiscovery")
        self.fakes.TestResult=self.fakes.TestResult+2

    def __init__(self,fakes):
        self._address = "initial value"
        self.fakes=fakes
  
    @property
    def Address(self):
        return self._address
  
    @Address.setter
    def Address(self, value):
        self._address = value
        self.PropertiesChanged("BluetoothAudioBridge.FakeDbusBluezObject.Adapter1", {"Address": self._address}, [])
  
    PropertiesChanged = signal()

class TestFakeDbusBluezDevice():
    dbus="""
       <node>
         <interface name='BluetoothAudioBridge.FakeDbusBluezObject.Device1'>
           <method name='Connect'>
           </method>
           <method name='Disconnect'>
           </method>
           <method name='Pair'>
           </method>
           <property name="Address" type="s" access="read">
           </property>
           <property name="Trusted" type="b" access="readwrite">
           </property>
         </interface>
       </node>"""

    def Connect(self):
        """connect"""
        print("connect")
        self.fakes.TestResult=self.fakes.TestResult+1

    def Disconnect(self):
        """disconnect"""
        print("disconnect")
        self.fakes.TestResult=self.fakes.TestResult+2

    def Pair(self):
        """pair"""
        print("pair")
        self.fakes.TestResult=self.fakes.TestResult+4

    def __init__(self,fakes):
        self._address = "initial value"
        self._trusted = false
        self.fakes=fakes
  
    @property
    def Address(self):
        return self._address
  
    @Address.setter
    def Address(self, value):
        self._address = value
        self.PropertiesChanged("BluetoothAudioBridge.FakeDbusBluezObject.Device1", {"Address": self._address}, [])
  
    @property
    def Trusted(self):
        self.fakes.TestResult=self.fakes.TestResult+8
        return self._trusted

    @Trusted.setter
    def Trusted(self, value):
        self._trusted = value
        self.PropertiesChanged("BluetoothAudioBridge.FakeDbusBluezObject.Device1", {"Trusted": self._trusted}, [])

    PropertiesChanged = signal()



class TestFakeMethods():
    def __init__(self,bluetoothAudioBridge):
        self.TestResult = 0
        self.broker = None
        self.bluetoothAudioBridge=bluetoothAudioBridge
        self.bluetoothAudioBridge.DbusBluezPath = "BluetoothAudioBridge.FakeDbusObject"
        self.bluetoothAudioBridge.MqttServer = mqttServer
        self.bluetoothAudioBridge.MqttUsername = mqttUsername
        self.bluetoothAudioBridge.MqttPassword = mqttPassword
        self.fakeDbusObject = None

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
           self.TestResult=1
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

    async def startTestFakeDbusBluezAdapter(self):
        bus = SessionBus()
        if (self.fakeDbusObject):
            self.fakeDbusObject.unpublish()
        self.fakeDbusObject =  bus.publish(self.bluetoothAudioBridge.DbusBluezPath,("hci0", TestFakeDbusBluezAdapter(self)))

    async def startTestFakeDbusBluezDevice(self):
        bus = SessionBus
        if (self.fakeDbusObject):
            self.fakeDbusObject.unpublish()
        self.fakeDbusObject =  bus.publish(self.bluetoothAudioBridge.DbusBluezPath,)
        bus.publish(self.bluetoothAudioBridge.DbusBluezPath,
             ("hci0", TestFakeDbusBluezAdapter(self))
             ("hci0/dev_aa_12_00_41_aa_00", TestFakeDbusBluezDevice(self)))

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
        self.bus = SessionBus()
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

    def test_listMockedDbusEntries(self):
        self.loop.run_until_complete(self.fakes.startTestFakeDbusBluezAdapter())
        
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerDbus())
        self.loop.run_until_complete(asyncio.sleep(5))
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())
        #self.assertTrue(self.fakes.BridgeWorks)


    def test_detectMockedBluetoothDevice(self):
        self.loop.run_until_complete(self.fakes.startTestFakeDbusBluezAdapter())
        
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerDbus())
        self.loop.run_until_complete(asyncio.sleep(5))
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())


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

