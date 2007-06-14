#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import sys, os, os.path, socket, subprocess, re, time, signal
import errno
from datetime import timedelta, datetime
from logging import info, debug, warn, error, critical

# umic-mesh imports
from um_application import Application
from um_config import *
from um_ssh import *


class Measurement(Application):
    """Framework for UMIC-Mesh measurements

       For an example how to use this class, see um_ping-test.py.

       To implement your own measurements, derive from this class and add
       test_* methods which implement the various measurements. These test
       methods will be executed on a call to Measurement.run() in no particular
       order.

       To execute commands on a remote host, the method remote_execute can be
       used. A timeout setting prevents infinite running remote commands.

       FIXME: Document the concepts "run" and "iteration"
    """

    # Some bash code to implement a timelimit for a program run in background
    TimeoutCommand = """
        function sigchld() {
        if ! ps $BGPID 2>&1 >/dev/null; then
                wait $BGPID; export EXITSTATUS=$?;
            fi;
        };

        set +H # Disable !  style history substitution
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
        """

    def __init__(self):
        Application.__init__(self)

        # Object variables
        self.LogFile = ""
        self.Connections = {}
        self.TestMethods = self.get_test_methods()

        self.tcpdump = None
        self.tcpdump_proc = {}

        # initialization of the option parser
        usage = "usage: %prog [options] NODES\n" \
                "where NODES := either [v]mrouter numbers or hostnames"

        self.parser.set_usage(usage)
        self.parser.set_defaults(asymmetric = False, device = 'ath0',
                                 hostnameprefix = 'mrouter', tscale = 1,
                                 runs = 1, iterations = 1, output_dir = '.',
                                 ignore_critical = False,  abort_run = False,
                                 unified_log = False, wipe_out = False)

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
        self.parser.add_option("-C", "--ignore-critical", action = "store_true", dest = "ignore_critical",
                               help = "ignore critical errors like ssh being immune to SIGKILL, etc.")
        self.parser.add_option("-k", "--abort_run",
                               action = "store_true", dest = "abort_run",
                               help = "if run comprises several tests abort a run if a single test fails  [default: %default]")
        self.parser.add_option("-R" , "--runs", metavar = "#", type = int,
                               action = "store", dest = "runs",
                               help = "set number of test runs in a row [default: %default]")
        self.parser.add_option("-t" , "--tscale", metavar = "#.#", type = float,
                               action = "store", dest = "tscale",
                               help = "set factor to scale watchdog timers [default: %default]")
        self.parser.add_option("-u", "--unified-log",
                               action = "store_true", dest = "unified_log",
                               help = "if a run comprises several tests store ouput in one file  [default: %default]")
        self.parser.add_option("-O" , "--output", metavar = "dir",
                               action = "store", dest = "output_dir",
                               help = "set the directory to write log files to [default: %default]")
        self.parser.add_option("-w" , "--wipe-out",
                               action = "store_true", dest = "wipe_out",
                               help = "create a fresh output directory [default: %default]")

        # FIXME: Add documentation:
        # Every such script will be terminated at the end of the run/iteration/test
        # A run/test cript is started with following additional parameters:
        #       log-string source target
        # A iteration script is started with additional parameters
        #       log-string nodes
        self.parser.add_option("--run-script", metavar ="SCRIPT",
                               action = "store", dest = "run_script",
                               help = "Script to execute for every run.")
        self.parser.add_option("--run-script-at", metavar = "TARGET",
                               action = "store", dest = "run_script_at",
                               help = "One of 'source', 'target'")

        self.parser.add_option("--iteration-script", metavar ="SCRIPT",
                               action = "store", dest = "iteration_script",
                               help = "Script to execute for every iteration")
        self.parser.add_option("--iteration-script-at", metavar = "TARGET",
                               action = "store", dest = "iteration_script_at",
                               help = "One of 'all' or a hostname")

        self.parser.add_option("--test-script", metavar ="SCRIPT",
                               action = "store", dest = "test_script",
                               help = "Script to execute for every test")
        self.parser.add_option("--test-script-at", metavar = "TARGET",
                               action = "store", dest = "test_script_at",
                               help = "One of 'source', 'target'")


    def set_option(self):
        "Set options"

        Application.set_option(self)

        # correct numbers of arguments?
        if len(self.args) < 2:
            self.parser.error("Incorrect number of arguments. Need at least two nodes!")


    def remote_start(self, node, command, **kwargs):
        # Open an SSH connection if none is open yet and keep it open over the
        # end of this method
        self.Connections[node] = self.Connections.get(node, SshConnection(node))
        conn = self.Connections[node]

        return conn.execute(command, **kwargs)

    def remote_stop(self, conn, timeout = 1):
        # FIXME: This ecould block the whole measurement ...
        # FIXME Documentation: Changes signal handler
        limited_wait = TimeoutFunction(proc.wait, timeout)
        rc = None
        try:
            os.kill(proc.pid, signal.SIGTERM)
            limited_wait
            return signal.SIGTERM
        except TimeoutFunctionException:
            try:
                os.kill(proc.pid, signal.SIGKILL)
                limited_wait
                return signal.SIGKILL
            except TimeoutFunctionException:
                return None

    # FIXME: Add support for other usernames
    def remote_execute(self, node, command, timeout, suppress_output=False):
        """ Run command at some node via ssh.

        command may last at most timeout seconds and may not contain ' at the
        moment. This is considered a FIXME.

        If program terminates in time, return exit status of the program. If we
        needed to kill the SSH connection, return -1.
        """

        timeout = timeout * self.options.tscale

        if not suppress_output:
            info("Calling \"%s\" on %s (timeout %i seconds)" % (command, node, timeout))

        if self.options.debug:
            os.write(self.LogFile,
                     "### command=\"%s\" (timeout %i, suppress_output = %s)\n"
                     % (command, timeout, str(suppress_output)))

        ssh_command = self.TimeoutCommand % (command, timeout * 10)

        null = open(os.devnull)
        if suppress_output:
            log = null
        else:
            log = self.LogFile

        debug("Calling \"%s\" on %s (timeout %i seconds)" % (str(command), node, timeout))
        # FIXME: Is there a reason, we need an interactive bash?
        proc = self.remote_start(node, "bash -c '%s'" % ssh_command, bufsize=0,
                stdin=null, stdout=log, stderr=log)

        # Allow 4 seconds grace period for bash code execution
        grace_period = 4 * self.options.tscale;
        end_ts_ssh = datetime.now() + timedelta(seconds = timeout + grace_period)

        while datetime.now() < end_ts_ssh:
            if proc.poll() != None:
                return proc.returncode
            debug("sleeping...")
            time.sleep(1)

        warn("ssh still running after timeout.")
        rc = self.remote_stop(proc)
        if rc == signal.SIGTERM:
            warn("ssh terminated by SIGTERM")
        elif rc == signal.SIGKILL:
            warn("ssh terminated by SIGKILL")
        else:
            error("ssh still running after SIGKILL. Giving up.")

        return -1

    def sigterm(self):
        debug("SIGTERM caught.")

    def sigint(self):
        debug("SIGINT caught.")

    def host_pairs(self, hostnames = False):
        """ Returns all valid source host/target host pairs, for which tests
        should be run """
        prefix = self.options.hostnameprefix
        for target in self.args:
            for source in self.args:
                if source == target:
                    continue
                if self.options.asymmetric and source > target:
                    continue
                if hostnames:
                    yield (prefix + source, prefix + target)
                else:
                    yield (source, target)

    def get_test_methods(self):
        """ Collects all implemented test methods """
        methods = []
        for name  in dir(self):
            # TODO: check for valid signature
            if name.startswith("test_"):
                method = getattr(self, name)
                if callable(method):
                    methods.append(method)
        return methods

    def log_name(self, iteration, source, target, run, test_name):
        if self.options.unified_log or not test_name:
            return "i%02i_s%s_t%s_r%03i" % (iteration, source, target, run)
        else:
            return "i%02i_s%s_t%s_r%03i_%s" % (iteration, source, target, run, test_name)

    def log_open(self, iteration, source, target, run, test_name):
        file = log_name(self, iteration, source, target, run, test_name)
        return os.open(file, os.O_CREAT|os.O_APPEND|os.O_RDWR, 00664)

    def run(self):
        "Run the measurement"

        signal.signal(signal.SIGTERM, self.sigterm)

        start_ts_measurement = datetime.now()

        # Check available test methods
        if len(self.TestMethods) == 0:
            error("FATAL: no test methods.")
            sys.exit(1)                 # FIXME Replace by exception, please!
        if len(self.TestMethods) == 1:
            self.MultipleTests = False
            self.options.unified_log = True
        else:
            self.MultipleTests = True

        # Prepare output directory
        info("Preparing output directory...")
        try:
            os.makedirs(self.options.output_dir)
            os.chdir(self.options.output_dir)
        except os.error, inst:
            if inst.errno != errno.EEXIST or not os.path.isdir(self.options.output_dir):
                error("Failed to create directory: %s" % t)
                sys.exit(1)

        # Clean up output directory
        if self.options.wipe_out:
            for file in os.listdir("."):
                if os.path.isdir(file):
                    warn("Output directory contains a directory (%s)" % file)
                else:
                    try:
                        os.remove(file)
                    except os.error, inst:
                        warn("Failed remove %s: %s" % (file, t))

        try:
            for iteration in range(1, self.options.iterations + 1):
                info("Iteration %i: starting... "%(iteration))
                start_ts_iteration = datetime.now()

                for (source, target) in self.host_pairs(hostnames = True):

                    # iterate through runs
                    for run in range(1, self.options.runs + 1):

                        if self.MultipleTests:
                            info("start: run #%i (%i): %s -> %s"
                                    % (run, iteration, source, target))

                        start_ts_run = datetime.now()
                        run_ok = self.run_tests(iteration, source, target, run)

                        if self.MultipleTests:
                            if run_ok:
                                info("finished: run #%i (%i): %s -> %s (%s)"
                                        % (run, iteration, source, target,
                                            datetime.now() - start_ts_run))
                            else:
                                warn("FAILED: run #%i (%i): %s -> %s (%s)"
                                        % (run, iteration, source, target,
                                            datetime.now() - start_ts_run))

                info("Iteration %i: finished (%s)"
                        % (iteration, datetime.now() - start_ts_iteration))

            info("Overall runtime: %s" % (datetime.now() - start_ts_measurement))

        # TODO: Think about if to catch this exception in an inner loop to do... what?!
        except SshException:
            critical("Caught SshException. Giving up.")

    def run_tests(self, iteration, source, target, run):
        """ Run all tests for an iteration/source/target-pair. """

        def start_script(script, script_node, source, target, logstring):
            if not script:
                return None
            if script_node == 'source':
                node = source
            elif script_node == 'target':
                node = target
            else:
                # Fixme: Throw exception?
                return None
            return self.remote_start(node, script + " %s %s %s" % (logstring, source, target),
                    stdin=null, stdout=null, stderr=null)


        run_ok = True

        logstring = self.log_name(iteration, source, target, run, None)
        runscript_proc = start_script(self.options.test_script, self.options.test_script_at,
                source, target, logstring)

        for test in self.TestMethods:

            test_name = test.__name__.replace("test_", "", 1)

            self.LogFile = self.log_open(iteration, source, target, run, test_name)
            if self.MultipleTests:
                info("running test \"%s\""  % test_name)

            start_ts_test = datetime.now()

            logstring = self.log_name(iteration, source, target, run, test_name)
            testscript_proc = start_script(self.options.test_script, self.options.test_script_at,
                    source, target, logstring)

            test_ok = test(iteration, run, source, target)
            if test_ok:
                info("finished: test \"%s\" (%s)" % (test_name, datetime.now() - start_ts_test))
            else:
                warn("FAILED: test \"%s\" (%s)"  % (test_name, datetime.now() - start_ts_test))
                run_ok = False

            if testscript_proc:
                remote_stop(testscript_proc)

            os.fsync(self.LogFile)
            os.close(self.LogFile)

            if not test_ok:
                if self.options.abort_run:
                    break
                if self.MultipleTests:
                    info("Continuing run #%i..." % run)

        if runscript_proc:
            remote_stop(runscript_proc)

        return run_ok


class TimeoutFunctionException(Exception):
    """Exception to raise on a timeout"""
    pass

class TimeoutFunction:

    def __init__(self, function, timeout):
        self.timeout = timeout
        self.function = function

    def handle_timeout(self, signum, frame):
        raise TimeoutFunctionException()

    def __call__(self, *args):
        old = signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.timeout)
        try:
            result = self.function(*args)
        finally:
            signal.signal(signal.SIGALRM, old)
        signal.alarm(0)
        return result
