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
from pydbus import SystemBus
import unittest
from pydbus.generic import signal
from gi.repository import GLib, Gio


from core import BluetoothAudioBridge

class TestFakeObjectManager():
    # org.freedesktop.DBus.ObjectManager.GetManagedObjects (out DICT<OBJPATH,DICT<STRING,DICT<STRING,VARIANT>>> objpath_interfaces_and_properties);
    # org.freedesktop.DBus.ObjectManager.InterfacesAdded (OBJPATH object_path, DICT<STRING,DICT<STRING,VARIANT>> interfaces_and_properties);
    # org.freedesktop.DBus.ObjectManager.InterfacesRemoved (OBJPATH object_path, ARRAY<STRING> interfaces);
    dbus="""
       <node>
         <interface name='org.freedesktop.DBus.ObjectManager'>
           <method name='GetManagedObjects'>
             <arg type='a{oa{sa{sv}}}' name='objpath_interfaces_and_properties' direction='out'/>
           </method>
           <signal name="InterfacesAdded">
             <arg direction="out" type="o" name="object_path"/>
             <arg direction="out" type="a{sa{sv}}" name="interfaces_and_properties"/>
           </signal>
           <signal name="InterfacesRemoved">
             <arg direction="out" type="o" name="object_path"/>
             <arg direction="out" type="as" name="interfaces"/>
           </signal>
         </interface>
       </node>"""

    def ToVariant(self,pvalue):
        pvalueVariant = None
        if type(pvalue)==str:
           pvalueVariant=GLib.Variant('s',pvalue)
        if type(pvalue)==bytes:
           pvalueVariant=GLib.Variant('s',str(pvalue))
        if type(pvalue)==int:
           pvalueVariant=GLib.Variant('i',pvalue)
        if type(pvalue)==float:
           pvalueVariant=GLib.Variant('d',pvalue)
        if type(pvalue)==bool:
           pvalueVariant=GLib.Variant('b',pvalue)

    def GetManagedObjects(self):
        """get managed objects"""
        print("get managed objects")
        result = {}
        for path,obj in self.objects.items():
          resObj = {}
          node_info = type(obj).dbus
          node_info = Gio.DBusNodeInfo.new_for_xml(node_info)
          interfaces = node_info.interfaces
          for interface in interfaces:
             resInterface={}
             for p in interface.properties:
               pvalue = getattr(obj,p.name)
               pvalueVariant=GLib.Variant(p.signature,pvalue)
               if pvalueVariant==None:
                  print("could not convert value "+str(pvalue)+" of "+p.name+"("+ str(type(pvalue)) +")to a variant")
               else:
                  resInterface[p.name]=pvalueVariant
             resObj[interface.name]=resInterface
          result[path]=resObj
        return result

    def __init__(self,bus):
        self.bus=bus
        self.objects = {}
        self.registrations = {}

    def export(self,path,obj): 
        newRegistration=self.bus.register_object(path,obj,None)
        self.objects[path]=obj
        self.registrations[path]=newRegistration
  
    PropertiesChanged = signal()
    InterfacesAdded = signal()
    InterfacesRemoved = signal()


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
           <property name="Connected" type="b" access="read">
           </property>
           <property name="Trusted" type="b" access="readwrite">
           </property>
           <property name="UUIDs" type="as" access="read">
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
        self._connected = False
        self._trusted = False
        self._uuids = ['0000110b-0000-1000-8000-00805f9b34fb']
        self.fakes=fakes
  
    @property
    def Address(self):
        return self._address
  
    @Address.setter
    def Address(self, value):
        self._address = value
        self.PropertiesChanged("BluetoothAudioBridge.FakeDbusBluezObject.Device1", {"Address": self._address}, [])
  
    @property
    def Connected(self):
        return self._connected
  
    @Connected.setter
    def Connected(self, value):
        print("dummy-connection: "+str(value))
        self._connected = value
        self.PropertiesChanged("BluetoothAudioBridge.FakeDbusBluezObject.Device1", {"Connected": self._connected}, [])
  
    @property
    def Trusted(self):
        self.fakes.TestResult=self.fakes.TestResult+8
        return self._trusted

    @Trusted.setter
    def Trusted(self, value):
        self._trusted = value
        self.PropertiesChanged("BluetoothAudioBridge.FakeDbusBluezObject.Device1", {"Trusted": self._trusted}, [])
 
    @property
    def UUIDs(self):
        return self._uuids

    @UUIDs.setter
    def UUIDs(self, value):
        self._uuids = value
        self.PropertiesChanged("BluetoothAudioBridge.FakeDbusBluezObject.Device1", {"UUIDs": self._uuids}, [])

    PropertiesChanged = signal()



class TestFakeMethods():
    def __init__(self,bluetoothAudioBridge):
        self.TestResult = 0
        self.bluetoothAudioBridge=bluetoothAudioBridge
        self.bluetoothAudioBridge.DbusBluezBusName = "BluetoothAudioBridge.FakeDbusObject"
        self.bluetoothAudioBridge.DbusBluezObjectPath = "/BluetoothAudioBridge/FakeDbusObject/hci0"
        self.fakeDbusObject = None
        self.fakeDbusDevice = None
        self.bus = None
        self.bluetoothAudioBridge.DbusBluezOnSystemBus=False

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

    async def startTestFakeDbusBluezAdapter(self):
        if not self.bus:
            self.bus = SessionBus()
        if (self.fakeDbusObject):
            self.fakeDbusObject.unpublish()
            await asyncio.sleep(0.5)
        self.fakeDbusObject =  self.bus.publish(self.bluetoothAudioBridge.DbusBluezBusName,("hci0", TestFakeDbusBluezAdapter(self)))


    async def startTestFakeDbusBluezAdapterWithObjectManager(self):
        if not self.bus:
            self.bus = SessionBus()
        if (self.fakeDbusObject):
            self.fakeDbusObject.unpublish()
            await asyncio.sleep(0.5)
        #help(dbusName)
        #help(dbusObjectManager)
        #print(dbusObjectManager.get_property("connection"))
        #print(dbusObjectManager.get_property("object_path"))
        fakeObjectManager = TestFakeObjectManager(self.bus)
        fakeDbusAdapter = TestFakeDbusBluezAdapter(self)
        self.fakeDbusDevice = TestFakeDbusBluezDevice(self)
        fakeDbusDevice2 = TestFakeDbusBluezDevice(self)
        prefix = "/"+ self.bluetoothAudioBridge.DbusBluezBusName.replace(".","/")
        print(prefix)
        a=self.bus.register_object("/",fakeObjectManager,None)
        fakeObjectManager.export(prefix+"/hci0",fakeDbusAdapter)
        fakeObjectManager.export(prefix+"/hci0/dev_aa_12_00_41_aa_00",self.fakeDbusDevice)
        fakeObjectManager.export(prefix+"/hci0/dev_aa_12_00_41_aa_01",fakeDbusDevice2)
        dbusName=self.bus.request_name(self.bluetoothAudioBridge.DbusBluezBusName)
        #dbusObjectManager=Gio.DBusObjectManagerServer.new("/hci0")
        #dbusObjectManager.set_connection(self.bus.con)
        #a.unregister()
        #self.fakeDbusObject =  self.bus.publish(self.bluetoothAudioBridge.DbusBluezBusName,("hci0", TestFakeDbusBluezAdapter(self)))
        #self.fakeDbusObject =  dbusObjectManager.export("hci0", TestFakeDbusBluezAdapter(self))
        #help(self.fakeDbusDevice)
        #dbusObjectManager.export(self.fakeDbusDevice)
        #dbusName.unown()


    async def startTestFakeDbusBluezDevice(self):
        if not self.bus:
            self.bus = SessionBus()
        if (self.fakeDbusObject):
            self.fakeDbusObject.unpublish()
            await asyncio.sleep(0.5)
        self.fakeDbusDevice = TestFakeDbusBluezDevice(self)
        self.fakeDbusObject = self.bus.publish(self.bluetoothAudioBridge.DbusBluezBusName,
             ("hci0", TestFakeDbusBluezAdapter(self)),
             ("hci0/dev_aa_12_00_41_aa_00", self.fakeDbusDevice))
        await asyncio.sleep(0.5)

    async def stopTestFakeDbusBluezAdapterAndDevice(self):
        if (self.fakeDbusObject):
            self.fakeDbusObject.unpublish()
            self.fakeDbusDevice = None
            self.fakeDbusObject = None
            await asyncio.sleep(0.5)

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

    def test_startFakeObjectManager(self):
        self.loop.run_until_complete(self.fakes.startTestFakeDbusBluezAdapterWithObjectManager())
        self.loop.run_until_complete(asyncio.sleep(30))

    def atest_openFakeDbusAdapterFor30Seconds(self):
        self.loop.run_until_complete(self.fakes.startTestFakeDbusBluezAdapter()) 
        self.loop.run_until_complete(asyncio.sleep(30))

    def atest_detectMockedBluetoothDevice(self):
        self.bluetoothAudioBridge.dbusBtDeviceDetected=self.fakes.callerWithOneParameterWasCalledAsync()
        self.loop.run_until_complete(self.fakes.startTestFakeDbusBluezAdapter()) 
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerDbus())
        self.loop.run_until_complete(asyncio.sleep(2))
        self.loop.run_until_complete(self.fakes.startTestFakeDbusBluezDevice())
        self.loop.run_until_complete(asyncio.sleep(2))
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())
        self.loop.run_until_complete(self.fakes.stopTestFakeDbusBluezAdapterAndDevice())
        self.assertEqual(self.fakes.TestResult,1)

    def atest_removeMockedBluetoothDevice(self):
        self.bluetoothAudioBridge.dbusBtDeviceRemoved=self.fakes.callerWithOneParameterWasCalledAsync()
        self.loop.run_until_complete(self.fakes.startTestFakeDbusBluezAdapter())
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerDbus())
        self.loop.run_until_complete(asyncio.sleep(2))
        self.loop.run_until_complete(self.fakes.startTestFakeDbusBluezDevice())
        self.loop.run_until_complete(asyncio.sleep(2))
        self.loop.run_until_complete(self.fakes.startTestFakeDbusBluezAdapter()) 
        self.loop.run_until_complete(asyncio.sleep(2))
        self.loop.run_until_complete(self.fakes.stopTestFakeDbusBluezAdapterAndDevice())
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())
        self.assertEqual(self.fakes.TestResult,1)

    def atest_detectMockedBluetoothDeviceConnection(self):
        self.bluetoothAudioBridge.dbusBtDeviceConnected=self.fakes.callerWithOneParameterWasCalledAsync()
        self.loop.run_until_complete(self.fakes.startTestFakeDbusBluezDevice())
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerDbus())
        self.fakes.fakeDbusDevice.Connected=True
        self.loop.run_until_complete(asyncio.sleep(2))
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())
        self.loop.run_until_complete(self.fakes.stopTestFakeDbusBluezAdapterAndDevice())
        self.assertEqual(self.fakes.TestResult,1)

    def atest_detectMockedBluetoothDeviceDisconnection(self):
        self.bluetoothAudioBridge.dbusBtDeviceDisconnected=self.fakes.callerWithOneParameterWasCalledAsync()
        self.loop.run_until_complete(self.fakes.startTestFakeDbusBluezDevice())
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerDbus())
        self.fakes.fakeDbusDevice.Connected=True
        self.loop.run_until_complete(asyncio.sleep(2))
        self.fakes.fakeDbusDevice.Connected=False
        self.loop.run_until_complete(asyncio.sleep(2))
        self.loop.run_until_complete(self.bluetoothAudioBridge.unregister())
        self.loop.run_until_complete(self.fakes.stopTestFakeDbusBluezAdapterAndDevice())
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

