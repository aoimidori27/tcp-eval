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
        the execute method.

        SshConnection automatically manages MasterConnections in a pool for
        all instances of SshConnection.

        FIXME: Add keepalive setting, so a master connection stays alive even
        if all instances are destroyed (i.e. make execution of __del__
        optional)
    """

    AtexitRegistered = False
    Connections = {}

    # FIXME: Add pid to ControlPath?
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

        if not host in SshConnection.Connections:
            SshConnection.Connections[host] = 0
        else:
            SshConnection.Connections[host] += 1

        self.ensure_connection()

        if not SshConnection.AtexitRegistered:
            atexit.register(SshConnection.cleanup)
            SshConnection.AtexitRegistered = True

    def __del__(self):
        """ Destructor.

            Closes master connection if self is the last instance using this
            connection
        """
        host = self.Host
        if host not in SshConnection.Connections:
            return
        SshConnection.Connections[host] -= 1
        if SshConnection.Connections[host] == 0:
            cmd = SshConnection.DefaultCmd + [ "-qqO", "exit", host]
            prog = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdout, stderr) = prog.communicate()
            if prog.returncode != 0:
                error("Failed to close ssh master connection to %s (%s/%s)" % (host, stdout, stderr));
            else:
                self.Connections.pop(host)

    def ensure_connection(self):
        """ Ensures that a master connection exists """
        cmd = SshConnection.DefaultCmd + ["-O", "check", self.Host]
        if subprocess.call(cmd) == 0:
            debug("SSH Master Connection to node %s already exists" % self.Host)
            return
#        elif self.Connections[self.Host] > 0
#            warn("Master connection to node \"%s\" vanished. Re-establishing..." % self.Host)

        info("Creating ssh master connection to node " + self.Host);
        cmd = SshConnection.DefaultCmd + [
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
        """ Execute a command on the remote host.

            **kwargs is just passed to subprocess.Popen.

            Returns subprocess.Popen instance.
        """
        cmd = SshConnection.DefaultCmd + [ self.Host, command ]
        return subprocess.Popen(cmd, **kwargs)

    def cleanup(cls):
        """ Atexit handler.

            Closes all master connections.
        """
        debug("Closing ssh master connections.")
        for host in SshConnection.Connections.keys():
            cmd = SshConnection.DefaultCmd + [ "-qqO", "exit", host]
            prog = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdout, stderr) = prog.communicate()
            if prog.returncode != 0:
                error("Failed to close ssh master connection to %s (%s/%s)" % (host, stdout, stderr));
            else:
                SshConnection.Connections.pop(host)
    cleanup = classmethod(cleanup)
