#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import sys, os, os.path, subprocess, re, time, signal

from logging import info, debug, warning, error
from datetime import timedelta, datetime
 
# umic-mesh imports
from um_application import Application
from um_config import *


class um_measurement(Application):

    def __init__(self):
    
        # call the super constructor
        Application.__init__(self)
    
        # initialization of the option parser
        self.parser.set_usage("usage: %prog [options]" )
        
        self.parser.add_option(
                               "-N" , "--nodes", 
                               action = "store", 
                               type = int, 
                               metavar = "#", 
                               dest = "nodes", 
                               default = 2,
                               help = "Set range of mrouters to cover [default: %default]",
                           )

        self.parser.add_option(
                               "-a" , "--asymmetric", 
                               action = "store_true", 
                               dest = "asymmetric", 
                               default = False,
                               help = "Consider one way tests only [default: %default]"
                           )
        
        self.parser.add_option(
                               "-t" , "--timeout-scale", 
                               action = "store", 
                               type = float, 
                               metavar = "secs",
                               dest = "timeout_scale",
                               default = 1,
                               help = "Set factor to scale watchdog timers [default: %default]"
                           )

        self.parser.add_option(
                               "-R" , "--runs", 
                               action = "store", 
                               type = int, 
                               metavar = "#", 
                               dest = "runs", 
                               default = 1,
                               help = "Set number of test runs in a row [default: %default]",
                           )

        self.parser.add_option(
                               "-I" , "--iterations", 
                               action = "store", 
                               type = int, 
                               metavar = "#", 
                               dest = "iterations", 
                               default = 1, 
                               help = "Set number of test runs in a row [default: %default]"
                           )

        self.parser.add_option(
                               "-O" , "--output-directory", 
                               action = "store", 
                               metavar = "directory", 
                               dest = "output_directory", 
                               default = ".",
                               help = "Set the directory to write log files to [default: %default]"
                           )
        
        self.parser.add_option(
                               "-w" , "--wipe-out", 
                               action = "store_true", 
                               dest = "wipe_out", 
                               default = False,
                               help = "Create a fresh output directory [default: %default]"
                           )
        

    def set_option(self):
        
        Application.set_option(self)
        
      
    def ssh_mrouter(self, number, command, timeout, suppress_output=False):
        timeout = timeout * self.options.timeout_scale
        debug("Calling \"%s\" on mrouter%i (timeout %i seconds)" % (command, number, timeout))
        if self.options.debug:
            os.write(self.log_file,
                     "### command=\"%s\" (timeout %i, suppress_output = %s)\n" % (command, timeout, str(suppress_output)))

        command = """
function sigchld() { echo WHYAMIDONTCALLED; wait %%-; EXITSTATUS=$?; };
trap sigchld SIGCHLD;
( %s ) &;
for ((t=0;t<%d;t+=1)) do
  if ! jobs %%- >/dev/null 2>&1; then
    exit $EXITSTATUS;
  fi;
  sleep 0.1;
done;
echo -e "\\nWARNING: Test still running after timeout. Sending SIGINT...";
kill -s SIGINT %%-
sleep 2;
echo jobs3: $(jobs -r);
if [ -n "$(jobs -r)" ]; then
  echo -e "\\nWARNING: Test still running after SIGINT. Sending SIGTERM...";
  kill -s SIGTERM %%-;
  sleep 1;
  echo jobs4: $(jobs -r);
  if [ -n "$(jobs -r)" ]; then
    echo -e "\\nWARNING: Test still running after SIGTERM. Sending SIGKILL...";
    kill -KILL %%-;
    echo JOBS: $(jobs);
  fi
fi
exit 254
""" %(command,timeout*10)

        debug("command: %s" %command);
  
        ssh = [
               "ssh", "-o", "PasswordAuthentication=no", "-o", "NumberOfPasswordPrompts=0", 
                "mrouter%i" % number,
#                "schaffrath@goldfinger.informatik.rwth-aachen.de" , 
#                "localhost",
               command 
       ]

        null = open(os.devnull)
        if suppress_output:
            log = null
        else:
            log = self.log_file
            
        prog = subprocess.Popen(
                                ssh,
                                bufsize=0,
                                stdin=null,
                                stdout=log, 
                                stderr=log)

        end_ts_ssh = datetime.now() + timedelta(seconds=timeout + 6)

        while prog.poll() == None:
            time.sleep(0.1)
            if datetime.now() > end_ts_ssh:
                warning("ssh still running after timeout. Sending SIGTERM...")
                os.kill(prog.pid, signal.SIGTERM)
                time.sleep(3)
                if prog.poll() == None:
                    warning("ssh still running after SIGTERM. Sending SIGKILL...")
                    os.kill(prog.pid, signal.SIGKILL)
                    time.sleep(1)
                    if prog.poll() == None:
                        error("ssh still running after SIGKILL. Giving up...")

        return prog.returncode

        


    def main(self):

        self.parse_option()
        self.set_option()
    
        start_ts_measurement = datetime.now()
        
        # Prepare output directory
        info("Preparing output directory...")
        if not os.path.isdir(self.options.output_directory):
            try:
                os.makedirs(self.options.output_directory)
            except Exception, t:
                error("Failed to create directory: %s"%t)
                sys.exit(1)
        
        os.chdir(self.options.output_directory)

        if self.options.wipe_out:
            for file in os.listdir("."):
                if os.path.isdir(file):
                    warning("Output directory contains a directory (%s) - NOT FROM ME!" % file)
                else:
                    try:
                        os.remove(file)
                    except Exception, t:
                        warning("Failed remove %s: %s" % (file, t))

        # Test...
        # TODO: Add options to run iterations/runs in parallel
        for iteration in range(1,self.options.iterations+1):
            info("Iteration %i: starting... "%(iteration))
            start_ts_iteration = datetime.now()
            for source in range(1,self.options.nodes+1):
                for target in range(1,self.options.nodes+1):
                    if source < target or (not self.options.asymmetric and source != target):
                        for run in range(1,self.options.runs+1):
                            self.log_file = os.open("i%02i_s%02i_t%02i_r%03i" % (iteration, source, target, run), os.O_CREAT| os.O_APPEND|os.O_RDWR, 00664)
                            info("start: test #%i (%i): mrouter%i -> mrouter%i" % (run, iteration, source, target))
                            start_ts_run = datetime.now()
                            returncode = self.test(iteration, run, source, target)
                            if returncode != 0:
                                warning("FAILED: test #%i (%i): mrouter%i -> mrouter%i (%s) (returncode = %s)" % (run, iteration, source, target, datetime.now()-start_ts_run, str(returncode)))
                            else:
                                info("finished: test #%i (%i): mrouter%i -> mrouter%i (%s)" % (run, iteration, source, target, datetime.now()-start_ts_run))
                            os.fsync(self.log_file)
                            os.close(self.log_file)
            info("Iteration %i: finished (%s)" % (iteration, datetime.now()-start_ts_iteration))

        info("Overall runtime: %s" % (datetime.now()-start_ts_measurement))
    
