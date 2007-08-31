#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

import os
from logging import info, debug, warn, error, critical
from tempfile import mkstemp

# twisted imports
from twisted.internet import defer, threads
from twisted.web import xmlrpc

from um_rpcservice import RPCService
from um_functions import execute, CommandFailed
from um_node import Node


class Tcpdump(xmlrpc.XMLRPC):
    """Class for managing the packet capturin"""

    def __init__(self, parent = None):

        # Call super constructor
        xmlrpc.XMLRPC.__init__(self)

        self._name = "tcpdump"
        self._daemon = "/usr/sbin/tcpdump"


    def start(self, expression, interface):
        """ This function will be called within its own thread """

        # -Z?
        args = "-i %s -w - %s" % (interface, expression)
        cmd = [ "start-stop-daemon", "--start",  "--quiet",
                "--exec", self._daemon,
                "--",     args ]

        dir = "/mnt/scratch/%s/tcpdump" % Node(type_="meshrouter").hostname()

        try:
            os.mkdir(dir)
            temp_fd, temp_file = mkstemp(suffix=".pcap", dir=dir)

            proc = subprocess.Popen(cmd, stdout=temp_fd, stderr=subprocess.PIPE)
            (dummy, stderr) = proc.communicate()
            rc = proc.wait()

            if rc != 0:
                for line in stderr.splitlines():
                    error(" %s" %line)
            else:
                rc = temp_file
        except OSError, inst:
            rc = 255
            error(inst)

        return rc

    def stop(self):
        """ This function will be called within its own thread """

        cmd = [ "start-stop-daemon", "--stop",  "--quiet",
                "--exec", self._daemon,
                "--signal", "TERM",
                "--retry",  "5"]
        rc = 0
        try:
            (stdout, stderr) = execute(cmd, shell=False)
            debug(stdout)
        except CommandFailed, inst:
            rc = inst.rc
            error(inst)
            for line in inst.stderr.splitlines():
                error(" %s" %line)

        return rc

    def xmlrpc_start(self, expression, interface):
        return threads.deferToThread(self.start, expression, interface)


    def xmlrpc_stop(self):
        return threads.deferToThread(self.stop)
