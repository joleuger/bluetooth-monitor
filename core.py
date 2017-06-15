#!/usr/bin/python3

from pydbus import SessionBus
import asyncio, gbulb
from hbmqtt.client import MQTTClient, ClientException

class BluetoothAudioBridge:
    def __init__(self, loop):
        self.loop = loop
        self.DbusPulseAudioPath=""
        self.DbusBluezPath=""
        self.DBusBluezObject=None
        self.MqttPath="/BluetoothAudioBridge"
        self.MqttServer="localhost:1883"
        self.MqttUsername="vhost:username"
        self.MqttPassword="password"
        self.MqttClient=None
        self.MqttReceivingFuture=None
        self.Continue=True

    def mqttReceivedAutoPair(self,message):
        print("MQTT: received auto pair")

    async def mqttReceiving(self):
        while self.Continue:
            print("MQTT: wait for message")
            try:
                message=await self.MqttClient.deliver_message(timeout=1)
                print("MQTT: received message")
            except asyncio.TimeoutError:
                pass
        self.MqttReceivingFuture.set_result(True)

    @asyncio.coroutine
    def registerMqtt(self):
        self.MqttClient = MQTTClient()
        connectionUrl="mqtt://"+self.MqttServer
        yield from self.MqttClient.connect(connectionUrl)
        #register receiver
        self.MqttReceivingFuture=self.loop.create_future()
        asyncio.ensure_future(self.mqttReceiving())
        print("registered on MQTT")

    async def registerDbus(self):
        self.bus = SessionBus()
        print("registered on DBUS")
        

    async def register(self):
        await self.registerMqtt()
        self.registerDBus()

    async def unregister(self):
        self.Continue=False
        if (self.MqttReceivingFuture):
            await self.MqttReceivingFuture
            await self.MqttClient.disconnect()
        self.MqttReceivingFuture=None

