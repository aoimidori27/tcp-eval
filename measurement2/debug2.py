#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from um_measurement2 import measurement, tests

from twisted.python import log

#log.startLogging(sys.stderr)

class DebugMeasurementApp(measurement.Measurement2App):

    def main(self):
        self.parse_option()
        self.set_option()

        self.add_test(tests.SSHTestFactory("whoami", name="whoami", timeout=None))

        self.run()

if __name__ == "__main__":
    DebugMeasurementApp().main()

