#!/usr/bin/env python
# -*- coding: utf-8 -*

# python imports
import os
import sys
import subprocess
from logging import info, debug, warn, error

# umic-mesh imports
from um_config import *


class CommandFailed(Exception):
    """Convenience function to handle return/exit codes"""

    def __init__(self, cmd, rc, stderr = None):
        self.cmd = cmd
        self.rc  = rc
        self.stderr = stderr

    def __str__(self):
        return "Command %s failed with return code %d." %(self.cmd, self.rc)


def execute(cmd, shell, raiseError = True):
    """Execute a shell command, wait for command to complete and return stdout/stderr"""

    debug("Executing: %s" % cmd.__str__())
    prog = subprocess.Popen(cmd, shell = shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = prog.communicate()
    rc = prog.returncode
    if raiseError and rc != 0:
        raise CommandFailed(cmd, rc, stderr)

    return (stdout, stderr)


def call(cmd, shell, raiseError=True):
    """Call a shell command, wait for command to complete and return exit code"""

    debug("Executing: %s" % cmd.__str__())
    rc = subprocess.call(cmd, shell = shell)
    if raiseError and rc != 0:
        raise CommandFailed(cmd, rc)
    return rc


def execpy(arguments = []):
    """Function to execute a python script with arguments"""

    class SystemExitException(Exception):
        """Private exception for execpy"""

        def __init__(self, status):
            self.status = status

    def raiseException(status):
        """Just to raise the exception with status"""

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


class StrictStruct:
    """Imitiate a struct/record"""

    def __init__(self, list = None, **kwargs):
        """
        Takes two parameters:

        If "list" is not None, it gives the allowed entries in the struct.
        Else, the list of allowed entries will be extracted from the **kwargs argument:

        Usage examples:
            StrictStruct(['foo', 'bar'])
            StrictStruct(['foo', 'bar'], foo=1, bar=3)
            StrictStruct(foo=1, bar=3)
        """

        self.__dict__["_items"] = {}
        if list is None:
            for (k,v) in kwargs.iteritems():
                if k not in self.__dict__:
                    self._items[k] = v
        else:
            for i in list:
                if i not in self.__dict__:
                    self._items[i] = None
            
            for (k,v) in kwargs.iteritems():
                if k in self._items:
                    self._items[k] = v
                else:
                    raise AttributeError("'%s' instance has no attribute '%s'"
                            % (self.__class__, k))


    def __getattr__(self, name):
        try:
            return self._items[name]
        except KeyError, inst:
            raise AttributeError("'%s' instance has no attribute '%s'"
                    % (self.__class__, name))


    def __setattr__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value
        elif name in self._items:
            self._items[name] = value
        else:
            raise AttributeError("'%s' instance has no attribute '%s'"
                    % (self.__class__, name))


    def __str__(self):

        return "<%s: %r>" % (self.__class__, self._items)
