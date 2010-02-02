#!/usr/bin/env python
# -*- coding: utf-8 -*

# python imports
import sys
import os
import subprocess
from logging import info, debug, warn, error

def requireroot():
    """Check whether the current user is root or not. If the user is not root
       sys.exit() will be called. The sys.exit() function will raise the build-in
       exception "SystemExit". When it is not handled, the Python interpreter will
       exit
    """

    if not os.getuid() == 0:
        error("You must be root. Command failed.")
        sys.exit(1)

def requireNOroot():
    """Check whether the current user is root or not. If the user is root
       sys.exit() will be called. The sys.exit() function will raise the build-in
       exception "SystemExit". When it is not handled, the Python interpreter will
       exit
    """

    if os.getuid() == 0:
        error("You can not be root. Command failed.")
        sys.exit(1)

def execute(cmd, shell = True, raiseError = True, input = None):
    """Execute a shell command, wait for command to complete and return 
       stdout/stderr. If the parameter input is given, it will be use as
       stdin
    """

    std_in = None

    debug("Executing: %s" % cmd.__str__())
    if input:
        std_in = subprocess.PIPE
        
    prog = subprocess.Popen(cmd, shell = shell, stdin = std_in,
                            stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    (stdout, stderr) = prog.communicate(input)
                
    rc = prog.returncode
    if raiseError and rc != 0:
        raise CommandFailed(cmd, rc, stderr)

    return (stdout, stderr)

def call(cmd, shell = True, raiseError = True, noOutput = False, input = None):
    """Call a shell command, wait for command to complete and return exit code"""

    std_in = None
    std_out = None
    
    debug("Executing: %s" % cmd.__str__())    
    if input:
        std_in = subprocess.PIPE
    if noOutput:
        std_out = open(os.path.devnull, "w")           
        
    prog = subprocess.Popen(cmd, shell = shell, stdin = std_in, stdout = std_out)
    prog.communicate(input)

    rc = prog.returncode
    if raiseError and rc != 0:
        raise CommandFailed(cmd, rc)

    return rc

def execpy(arguments = []):
    """Function to execute a python script within python"""

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


class CommandFailed(Exception):
    """Convenience function to handle return/exit codes"""

    def __init__(self, cmd, rc, stderr = None):
        Exception.__init__(self)
        self.cmd = cmd
        self.rc  = rc
        self.stderr = stderr

    def __str__(self):
        return 'Command "%s" failed with return code %d: %s' %(self.cmd, self.rc, self.stderr)


class StrictStruct:
    """Imitiate a struct/record"""

    def __init__(self, list = None, **kwargs):
        """The StrictStruct constructor takes two parameters:

           If "list" is not None, it gives the allowed entries in the struct.
           Otherwise, the list of allowed entries will be extracted from the **kwargs argument.

           Examples:
             StrictStruct(['foo', 'bar'])
             StrictStruct(['foo', 'bar'], foo = 1, bar = 3)
             StrictStruct(foo = 1, bar = 3)
        """

        self.__dict__["_items"] = {}
        if list is None:
            for (k, v) in kwargs.iteritems():
                if k not in self.__dict__:
                    self._items[k] = v
        else:
            for i in list:
                if i not in self.__dict__:
                    self._items[i] = None

            for (k, v) in kwargs.iteritems():
                if k in self._items:
                    self._items[k] = v
                else:
                    raise AttributeError("'%s' instance has no attribute '%s'"
                            % (self.__class__, k))

    def __getitem__(self, name):
        try:
            return self._items[name]
        except KeyError:
            raise AttributeError("'%s' instance has no attribute '%s'"
                    % (self.__class__, name))

    def __setitem__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value
        elif name in self._items:
            self._items[name] = value
        else:
            raise AttributeError("'%s' instance has no attribute '%s'"
                    % (self.__class__, name))

    def keys(self):
        return self.__dict__["_items"].keys()

    def __str__(self):
        return "<%s: %r>" % (self.__class__, self._items)
