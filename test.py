#!/usr/bin/python3

import asyncio, gbulb
from pydbus import SessionBus
import unittest
from hbmqtt.broker import Broker

from core import BluetoothAudioBridge

class TestFakeMethods():
    def __init__(self):
        self.BridgeWorks = False
        self.broker = None

    @asyncio.coroutine
    def startFakeBroker(self):
        print("Start fake broker")
        defaultMqtt = {}
        defaultMqtt["listeners"]={}
        defaultMqtt["listeners"]["default"]={"max-connections":5,"type":"tcp" }
        defaultMqtt["listeners"]["my-tcp-1"]={"bind":"127.0.0.1:1883"}
        defaultMqtt["timeout-disconnect-delay"]=2
        defaultMqtt["auth"]={"plugins":["auth.anonymous"],"allow-anonymous":True }
        self.broker = Broker(defaultMqtt)
        yield from self.broker.start()

    @asyncio.coroutine
    def stopFakeBroker(self):
        yield from self.broker.shutdown()


class TestBridge(unittest.TestCase):
    def setUp(self):
        self.bus = SessionBus()
        gbulb.install()
        self.loop=asyncio.get_event_loop()
        self.fakes=TestFakeMethods()
        self.bluetoothAudioBridge=BluetoothAudioBridge(self.loop)

    def test_connectToMqttTestBroker(self):
        self.loop.run_until_complete(self.fakes.startFakeBroker())
        self.loop.run_until_complete(self.bluetoothAudioBridge.registerMqtt())
        self.loop.run_until_complete(asyncio.sleep(5))
        self.loop.run_until_complete(self.fakes.stopFakeBroker())
        self.assertTrue(self.fakes.BridgeWorks)

if __name__ == '__main__':
    unittest.main()

