#!/usr/bin/python3

from pydbus import SessionBus
import asyncio, gbulb
#from hbmqtt.client import MQTTClient, ClientException
import paho.mqtt.client as mqtt

class BluetoothAudioBridge:
    def __init__(self, loop):
        self.loop = loop
        self.DbusPulseAudioPath=""
        self.DbusBluezPath=""
        self.DBusBluezObject=None
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


    def trace(self,level,msg):
        if self.TraceLevel >= level:
           print(msg)

    async def awaitOrStop(self,future):
        done,pending = await asyncio.wait([self.CancellationToken, future],return_when=asyncio.FIRST_COMPLETED)
        firstFinished=next(iter(done))
        if firstFinished==self.CancellationToken:
            #Note: pending tasks are still running
            return (False,None)
        #print(firstFinished)
        #print(firstFinished.result())
        return (True,firstFinished.result())

    def makeConnect(self,message):
        print("MQTT: received connect")

    def makePairAndTrust(self,message):
        print("MQTT: received pair and trust")

    def makeScan(self,message):
        print("MQTT: received scan")

    async def mqttProcessMessages(self):
        while self.Continue:
            message=await self.MqttMessageQueue.get()
            print("MQTT: received message")
            if message.startswith("Connect"):
                self.mqttReceivedConnect(message)
            if message.startswith("Pair and trust"):
                self.mqttReceivedConnect(message)
            if message.startswith("Scan"):
                self.mqttReceivedScan(message)

    async def registerMqtt(self):
        def on_connect(client, userdata, flags, rc):
            print("Connected with result code "+str(rc))
            # Subscribing in on_connect() means that if we lose the connection and
            # reconnect then subscriptions will be renewed.
            client.subscribe("/BluetoothAudioBridge/commands")
        def on_message(client, userdata, msg):
            print(msg.topic+" "+str(msg.payload))
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
        def on_disconnect(client, userdata, rc):
            if rc != 0:
                print("Unexpected disconnection.")
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
        self.MqttReceivingFuture=None

