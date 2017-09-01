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

from configManager import BluetoothMonitorConfigManager

class TestFakeMethods():
    def __init__(self,bluetoothMonitorConfig):
        self.TestResult = 0
        self.bluetoothMonitorConfig=bluetoothMonitorConfig

    def callerWithOneParameterWasCalled(self):
        def methodCall(parameter):
           print("parameter "+str(parameter))
           self.TestResult=self.TestResult+1
        return methodCall

    def callerWithOneParameterWasCalledAsync(self):
        async def methodCall(parameter):
           print("parameter "+str(parameter))
           self.TestResult=self.TestResult+1
        return methodCall


class TestConfig(unittest.TestCase):
    def setUp(self):
        gbulb.install()
        self.loop=asyncio.get_event_loop()
        self.bluetoothMonitorConfig=BluetoothMonitorConfigManager(self.loop)
        self.fakes=TestFakeMethods(self.bluetoothMonitorConfig)

    def test_loadConfig(self):
        self.bluetoothMonitorConfig.appConfigFilePath = "example-config.yaml"
        self.bluetoothMonitorConfig.onLoadConfigHandler = self.fakes.callerWithOneParameterWasCalled()
        self.bluetoothMonitorConfig.loadConfig()
        self.assertEqual(self.fakes.TestResult,1)

    def test_watchConfig(self):
        self.bluetoothMonitorConfig.appConfigFilePath = "example-config.yaml"
        self.bluetoothMonitorConfig.onLoadConfigHandler = self.fakes.callerWithOneParameterWasCalled()
        self.bluetoothMonitorConfig.loadConfig()
        self.loop.run_until_complete(self.bluetoothMonitorConfig.startWatchConfig())
        self.loop.run_until_complete(asyncio.sleep(2))
        self.loop.run_until_complete(self.bluetoothMonitorConfig.stopWatchConfig())
        self.assertEqual(self.fakes.TestResult,1)

if __name__ == '__main__':
    unittest.main()

