#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
from logging import info, warn, debug
from twisted.internet import defer, reactor
import os

#umic-mesh imports
from um_twisted_functions import twisted_sleep
from um_measurement import measurement, tests
from um_node import Node

class TcpMeasurement(measurement.Measurement):
    """This Measurement script resembles measurement for flowgrind-next + lcd evaluation"""

    def __init__(self):
        """Constructor of the object"""
        self.logprefix=""
        measurement.Measurement.__init__(self)

    def set_option(self):
        """Set options"""
        measurement.Measurement.set_option(self)

    @defer.inlineCallbacks
    def run(self):
        """Main method"""

        # common options used for all tests
        opts = dict( flowgrind_cc = "reno",
                     flowgrind_bin = "flowgrind-lcd",
                     flowgrind_duration = 240,
                     flowgrind_warmup = 5,
                     )

        brokenhosts = ["mrouter12", "mrouter22", "mrouter23", "mrouter24", "mrouter28", "mrouter41", "mrouter43"]
        srchosts = [ "mrouter14" ]
        middlehosts = [ "mrouter15" ]
        # inner loop configurations
        runs = [
                 dict( run_label = r"src14-dst8", src=14, dst=8 ),
                 dict( run_label = r"src14-dst27", src=14, dst=27 ),
                 dict( run_label = r"src14-dst30", src=14, dst=30 ),
                 dict( run_label = r"src14-dst18", src=14, dst=18 ),
                 dict( run_label = r"src14-dst2", src=14, dst=2 )
               ]

        # repeat loop
        iterations  = range(1,20)

        # outer loop with different scenario settings
        scenarios   = [
        dict( scenario_label = "bulk",
            flowgrind_opts ="-n 2 -M s -F 1 -O b=TCP_LCD".split()),
        #dict( scenario_label = "rr-http",
        #    flowgrind_opts="-r 123456 -n 2 -G s=q,C,350 -G s=p,L,9055,115.17 -U 100000 -F1 -O b=TCP_LCD".split() ),
        #dict( scenario_label = "rr-smtp",
        #    flowgrind_opts="-r 654321 -n 2 -G s=q,U,500,20000 -G s=p,C,80 -F1 -O b=TCP_LCD".split() ),
        #dict( scenario_label = "rr-telnet",
        #    flowgrind_opts="-r 123654 -n 2 -G s=q,U,40,1000 -G s=q,U,40,1000 -F1 -O b=TCP_LCD,TCP_NODELAY -F2 b=TCP_NODELAY".split() ),
        #dict( scenario_label = "limited-normal-800kbs",
        #    flowgrind_opts="-r 987654 -n 2 -G s=g,N,0.08192,0.1 -F1 -O b=TCP_LCD,TCP_NODELAY -F2 b=TCP_NODELAY".split() ),
        ]

        # configure testbed

        yield self.switchTestbedProfile("flowgrind_lcd_evaluation")

        allhosts = map(lambda x: "mrouter%s" %x, range(1,45))

        for host in brokenhosts:
            allhosts.remove(host)

        # adjust routing
        yield self.remote_execute_many(allhosts, "sudo ip route del 169.254.9.0/24 dev ath0")
        yield self.remote_execute_many(allhosts, "sudo ip route del default via 137.226.54.1 dev eth0")
        yield self.remote_execute_many(allhosts, "sudo ip route del default via 137.226.54.1 dev eth0")

        yield self.remote_execute_many(srchosts, "sudo ip route add 169.254.9.15 dev ath0")
        yield self.remote_execute_many(srchosts, "sudo ip route add 169.254.9.0/24 via 169.254.9.15")

        yield self.remote_execute_many(middlehosts, "sudo ip route add 169.254.9.14 dev ath0")
        # wait a few minutes to let olsr converge
        yield twisted_sleep(2)

        for scenario_no, scenario in enumerate(scenarios):
            kwargs = dict()
            kwargs.update(scenario)
            for it in iterations:
                for run_no, run in enumerate(runs):
                    # merge parameter configuration for the tests
                    kwargs.update(runs[run_no])
                    kwargs.update(opts)
                    target_dir = "%s/%s/%s" %(self.options.log_dir,scenario['scenario_label'],run['run_label'])
                    if not os.path.exists(target_dir):
                            os.makedirs(target_dir)
                    self.logprefix="%s/%s/i%03u" %(scenario['scenario_label'],run['run_label'], it)


                    # set source and dest for tests
                    kwargs['flowgrind_src'] = kwargs['src']
                    kwargs['flowgrind_dst'] = kwargs['dst']

                    # actually run tests
                    yield self.run_test(tests.test_flowgrind, **kwargs)

        # return to status quo
        yield self.switchTestbedProfile("minimum")

        yield self.tear_down()
        reactor.stop()

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()
        reactor.run()


if __name__ == "__main__":
    TcpMeasurement().main()

