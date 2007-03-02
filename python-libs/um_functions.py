#!/usr/bin/env python
#g -*- coding: utf-8 -*-

# python imports
import subprocess, os, sys, re
from logging import info, debug, warn, error
from socket import gethostname

# umic-mesh imports
from um_config import *


class CommandFailed(Exception):
    "Convenience function to handle returncodes"

    def __init__(self, cmd, rc, stderr = None):
        self.cmd = cmd
        self.rc  = rc
        self.stderr = stderr

    def __str__(self):
        return "Command %s failed with return code %d." %(self.cmd, self.rc)


def execute(cmd, shell, raiseError=True):
    "Excecute a shell command, "

    debug("Executing: %s" % cmd.__str__())
    prog = subprocess.Popen(cmd, shell = shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = prog.communicate()
    rc = prog.returncode
    if raiseError and rc != 0:
        raise CommandFailed(cmd, rc, stderr)

    return (stdout, stderr)


def call(cmd, shell, raiseError=True):
    "Call a shell command, wait for command to complete."

    debug("Executing: %s" % cmd.__str__())
    rc = subprocess.call(cmd, shell = shell)
    if raiseError and rc != 0:
        raise CommandFailed(cmd, rc)


def execpy(arguments = []):
    "Function to execute a python script with arguments"

    class SystemExitException(Exception):
        "Private exception for execpy"

        def __init__(self, status):
            self.status = status

    def raiseException(status):
        "Just to raise the exception with status"

        raise SystemExitException(status)

    global __name__;

    rc = 0

    # script is first argument
    script = arguments[0]

    # save argument list
    save_argv = sys.argv

    # save function pointer for sys.exit()
    save_exit = sys.exit

    # save __name__
    save_name = __name__;

    # override argument list
    sys.argv = arguments
    
    # override sys.exit()
    sys.exit = raiseException

    # override __name__
    __name__ = "__main__"

    try:
        info ("Now running %s " % script)
        execfile(script, globals())
    except SystemExitException, inst:
        info ("Script %s exited with sys.exit(%d)"
              % (script, inst.status))
        rc = inst.status

    if rc != 0:
        warn("Returncode: %d." % rc)

    # restore environment
    sys.exit = save_exit
    sys.argv = save_argv
    __name__ = save_name

    return rc


def requireroot():
    "Check if user is root"

    if not os.getuid() == 0:
        error("You must be root. Operation not permitted.")
        sys.exit(1)
