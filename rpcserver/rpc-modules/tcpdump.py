#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

import os
import errno
import re
import signal
import subprocess

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

        if os.path.exists("/usr/local/sbin/tcpdump"):
            self._daemon = "/usr/local/sbin/tcpdump"
        else:
            self._daemon = "/usr/sbin/tcpdump"

        self._name = "tcpdump"
        self._proc = None


    def start(self, iface, expr):
        # -Z?
        cmd = [self._daemon, "-i", iface, "-w", "-", expr]

#        dir = "/mnt/scratch/%s/tcpdump" % Node(type_="meshrouter").hostname()
        dir = "/tmp"

        try:
            os.mkdir(dir)
            os.chmod(dir, 0777)
        except OSError, inst:
            if inst.errno == errno.EEXIST:
                pass
            else:
                error(inst)
                return (255, "")

        try:
            temp_fd, temp_file = mkstemp(suffix=".pcap", dir=dir)


            self._proc = subprocess.Popen(cmd, stdout=temp_fd, stderr=subprocess.PIPE)
            # This expects tcpdump to output an line like
            #   tcpdump: listening on eth1, link-type EN10MB (Ethernet), capture size 96 bytes
            # as first output on stderr ...
            line = self._proc.stderr.readline()
            if re.search("listening on.*link-type", line):
                rc = 0;
            else:
                error("Tcpdump failed:")
                error(line)
                rc = self._proc.wait()
        except OSError, inst:
            rc = 255
            error(inst)

        return (rc, temp_file)

    def stop(self):
        """ This function will be called within its own thread """

        cmd = [ "start-stop-daemon", "--stop",  "--quiet",
                "--exec", self._daemon,
                "--signal", "TERM",
                "--retry",  "5"]
        rc = 0
        try:
            (stdout, stderr) = execute(cmd, shell=False)
            self._proc.wait()
            debug(stdout)
        except CommandFailed, inst:
            rc = inst.rc
            error(inst)
            for line in inst.stderr.splitlines():
                error(" %s" %line)

        return rc

    def xmlrpc_start(self, iface, expr):
        return threads.deferToThread(self.start, iface, expr)


    def xmlrpc_stop(self):
        return threads.deferToThread(self.stop)
