#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import sys, os, os.path, subprocess, re, time, signal
from datetime import timedelta, datetime
from logging import info, debug, warn, error
 
# umic-mesh imports
from um_application import Application
from um_config import *


class Measurement(Application):
    "Framework for UMIC-Mesh measurements"

    def __init__(self):
        "Constructor of the object"
    
        Application.__init__(self)
    
        # initialization of the option parser
        usage = "usage: %prog [options] NODES\n" \
                "where NODES := either [v]mrouter numbers or hostnames"
        
        self.parser.set_usage(usage)
        self.parser.set_defaults(asymmetric = False, device = 'ath0',
                                 hostnameprefix = 'mrouter', tscale = 1,
                                 runs = 1, iterations = 1, output_dir = '.',
                                 wipe_out = False)

        self.parser.add_option("-a" , "--asymmetric", 
                               action = "store_true", dest = "asymmetric", 
                               help = "consider one way tests only [default: %default]")
        self.parser.add_option("-d", "--dev",  metavar = "DEV",
                               action = "store", dest = "device",
                               help = "device on which the test should be [default: %default]")
        self.parser.add_option("-H", "--hprefix",  metavar = "NAME",
                               action = "store", dest = "hostnameprefix",
                               help = "hostname prefix for the node IDs [default: %default]")
        self.parser.add_option("-I" , "--iterations", metavar = "#", type = int,
                               action = "store", dest = "iterations", 
                               help = "set number of test runs in a row [default: %default]")
        self.parser.add_option("-R" , "--runs", metavar = "#", type = int,
                               action = "store", dest = "runs", 
                               help = "set number of test runs in a row [default: %default]")
        self.parser.add_option("-t" , "--tscale", metavar = "SEC", type = float, 
                               action = "store", dest = "tscale",
                               help = "set factor to scale watchdog timers [default: %default]")
        self.parser.add_option("-O" , "--output", metavar = "dir",
                               action = "store", dest = "output_dir", 
                               help = "set the directory to write log files to [default: %default]")
        self.parser.add_option("-w" , "--wipe-out", 
                               action = "store_true", dest = "wipe_out", 
                               help = "create a fresh output directory [default: %default]")


    def set_option(self):
        "Set options"
        
        Application.set_option(self)
        
        # correct numbers of arguments?
        if len(self.args) < 2:
            self.parser.error("Incorrect number of arguments. Need at least two Nodes!")
                
      
    def ssh_node(self, node, command, timeout, suppress_output=False):
        "Run command at ssh login"
        
        timeout = timeout * self.options.tscale
        
        debug("Calling \"%s\" on %s (timeout %i seconds)" % (command, node, timeout))
        
        if self.options.debug:
            os.write(self.log_file,
                     "### command=\"%s\" (timeout %i, suppress_output = %s)\n"
                     % (command, timeout, str(suppress_output)))

        #######################
        ### Begin BASH code ###

        command = """
        function sigchld() { 
        if ! ps $BGPID 2>&1 >/dev/null; then
                wait $BGPID; export EXITSTATUS=$?; 
            fi;
        };

        set +H
        trap sigchld SIGCHLD;
        (%s) &
        BGPID=$!;

        for ((t=0;t<%d;t+=1)) do
            if ! ps $BGPID >/dev/null 2>&1; then
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
        """ %(command, timeout * 10)
        
        #### Begin BASH code ###
        ########################
  
        ssh = ["ssh", "-o", "PasswordAuthentication=no","-o", 
               "NumberOfPasswordPrompts=0", node, "bash -i -c '%s'" %command]

        null = open(os.devnull)
        if suppress_output:
            log = null
        else:
            log = self.log_file
            
        prog = subprocess.Popen(ssh, bufsize=0, stdin=null, stdout=log, stderr=log)

        end_ts_ssh = datetime.now() + timedelta(seconds = timeout + 6)

        while prog.poll() == None:
            time.sleep(0.1)
            if datetime.now() > end_ts_ssh:
                warn("ssh still running after timeout. Sending SIGTERM...")
                os.kill(prog.pid, signal.SIGTERM)
                time.sleep(3)
                if prog.poll() == None:
                    warn("ssh still running after SIGTERM. Sending SIGKILL...")
                    os.kill(prog.pid, signal.SIGKILL)
                    time.sleep(1)
                    if prog.poll() == None:
                        error("ssh still running after SIGKILL. Giving up...")

        return prog.returncode


    def test(self, iteration, run, source, target):
        "Bla Bla"
        
        raise NotImplementedError("Bla Bla")


    def run(self):
        "Run the mesurement"
  
        start_ts_measurement = datetime.now()
        
        # prepare output directory
        info("Preparing output directory...")
        if not os.path.isdir(self.options.output_dir):
            try:
                os.makedirs(self.options.output_dir)
            except Exception, t:
                error("Failed to create directory: %s" % t)
                sys.exit(1)
        
        os.chdir(self.options.output_dir)

        # clean up output directory 
        if self.options.wipe_out:
            for file in os.listdir("."):
                if os.path.isdir(file):
                    warn("Output directory contains a directory (%s)" % file)
                else:
                    try:
                        os.remove(file)
                    except Exception, t:
                        warn("Failed remove %s: %s" % (file, t))


        # TODO: Add options to run iterations/runs in parallel
        for iteration in range(1, self.options.iterations + 1):
            info("Iteration %i: starting... "%(iteration))
            start_ts_iteration = datetime.now()
            
            for source in self.args:
                # for convenience convert node IDs to hostnames
                if source.isdigit():
                    source = "%s%s" %(self.options.hostnameprefix, source)
                
                for target in self.args:
                    # for convenience convert node IDs to hostnames
                    if target.isdigit():
                        target =  "%s%s" %(self.options.hostnameprefix, target)
                    
                    # ignore self connections
                    if source == target:
                        continue

                    # if asymmetric then only test source < target
                    if self.options.asymmetric and (source > target):
                        continue

                    # iterate through runs
                    for run in range(1, self.options.runs + 1):
                        self.log_file = os.open("i%02i_s%s_t%s_r%03i" %
                                                (iteration, source, target, run),
                                                os.O_CREAT|os.O_APPEND|os.O_RDWR, 00664)
                        
                        info("start: test #%i (%i): %s -> %s"
                             % (run, iteration, source, target))
                        
                        start_ts_run = datetime.now()
                        
                        if self.test(iteration, run, source, target):
                            info("finished: test #%i (%i): %s -> %s (%s)"
                                 % (run, iteration, source, target,
                                    datetime.now() - start_ts_run))
                        else:
                            warn("FAILED: test #%i (%i): %s -> %s (%s)"
                                 % (run, iteration, source, target,
                                    datetime.now() - start_ts_run))
                            
                            os.fsync(self.log_file)
                            os.close(self.log_file)
            
            info("Iteration %i: finished (%s)" 
                 % (iteration, datetime.now() - start_ts_iteration))

        info("Overall runtime: %s" % (datetime.now() - start_ts_measurement))  
