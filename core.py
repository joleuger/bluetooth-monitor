#!/usr/bin/python3

from pydbus import SessionBus
import asyncio, gbulb
from hbmqtt.client import MQTTClient, ClientException

class BluetoothAudioBridge:
    def __init__(self, loop):
        self.loop = loop
        self.DbusPulseAudioPath=""
        self.DbusBluezPath=""
        self.MqttPath="/BluetoothAudioBridge"
        self.MqttServer="localhost"
        self.MqttUsername="user"
        self.MqttPassword="password"
        self.MqttClient=None

    def mqttReceivedAutoPair(self,message):
        print("MQTT: received auto pair")

    @asyncio.coroutine
    def mqttReceiving(self):
        while True:
            print("MQTT: wait for message")
            message=yield from self.MqttClient.deliver_message()
            print("MQTT: received message")

    @asyncio.coroutine
    def registerMqtt(self):
        self.MqttClient = MQTTClient()
        connectionUrl="mqtt://"+self.MqttServer
        yield from self.MqttClient.connect(connectionUrl)
        #register receiver
        asyncio.ensure_future(self.mqttReceiving())
        print("registered on MQTT")

    def registerDbus(self):
        this.bus = SessionBus()
        print("registered on DBUS")

    async def register(self):
        await self.registerMqtt()
        self.registerDBus()

