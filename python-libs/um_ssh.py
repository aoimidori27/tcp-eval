#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import subprocess
import atexit
from logging import info, debug, warn, error, critical

class SshException(Exception):
    def __init__(self, prog = None):
        self.prog = prog

    def __str__(self):
        if self.prog == None:
            return "None"
        else:
            return "stdout = \"" + self.prog.stdout + "\", stderr = \"" + self.prog.stderr + "\""


class SshConnection:
    """
        Implements an interface for SSH with Master Connections.

        After creating an instance, you can just execute remote commands via
        the execute methode.

        SshConnection automatically manages MasterConnections in a pool for
        all instances of SshConnection.

    """

    AtexitRegistered = False
    Connections = {}

    DefaultCmd = ["ssh",
            "-o", "BatchMode=yes",
            "-o", "ConnectionAttempts=1",
            "-o", "ConnectTimeout=2",
            "-o", "StrictHostKeyChecking=no",
            # FIXME: pid mit einbauen!
            "-o", "ControlPath=%s-%%r@%%h:%%p" % socket.gethostname()
            ]


    def __init__(self, host):
        self.Host = host

        if not host in SshConnections.Connections:
            SshConnections.Connections[host] = 0
        else:
            SshConnections.Connections[host] += 1

        self.ensure_connection()

        if not SshConnections.AtexitRegistered:
            atexit.register(SshConnections.cleanup)
            SshConnections.AtexitRegistered = True


    def __del__(self):
        host = self.Host
        SshConnections.Connections[host] -= 1
        if SshConnections.Connections[host] == 0:
            cmd = SshConnections.DefaultCmd + [ "-qqO", "exit", host]
            prog = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdout, stderr) = prog.communicate()
            if prog.returncode != 0:
                error("Failed to close ssh master connection to %s (%s/%s)" % (host, stdout, stderr));
            else:
                self.Connections.pop(host)


    def ensure_connection(self):
        cmd = SshConnections.DefaultCmd + ["-O", "check", self.Host]
        if subprocess.call(cmd) == 0:
            return
#        elif self.Connections[self.Host] > 0
#            warn("Master connection to node \"%s\" vanished. Re-establishing..." % self.Host)

        debug("Creating ssh master connection to node " + self.Host);
        cmd = SshConnections.DefaultCmd + [
               "-o", "ControlMaster=yes",
               "-N", # Do not execute a remote command
               "-n", # Redirects stdin from /dev/null
               "-f", # Background execution
               self.Host]
        print " ".join(cmd)
        if subprocess.call(cmd) != 0:
            error("Failed to setup ssh master connection.")
            ### TODO: What to do here?
#            if not self.options.ignore_critical:
            raise SshException

        self.Connections[self.Host] = True


    def execute(self, command, **kwargs):
        cmd = SshConnections.DefaultCmd + [ self.Host, command ]
        return subprocess.Popen(cmd, **kwargs)

    def cleanup(cls):
        debug("Closing ssh master connections.")
        for host in SshConnections.Connections.keys():
            cmd = SshConnections.DefaultCmd + [ "-qqO", "exit", host]
            prog = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdout, stderr) = prog.communicate()
            if prog.returncode != 0:
                error("Failed to close ssh master connection to %s (%s/%s)" % (host, stdout, stderr));
            else:
                SshConnections.Connections.pop(host)
    cleanup = classmethod(cleanup)
