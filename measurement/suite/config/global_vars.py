#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

class global_vars:
    def __init__(self, offset):
        self.testbed_profile = "vmesh_schulte"

        # this must be adjusted for the specific measurement
        self.node_type = "vmeshrouter"

        # common options used for all tests
        self.opts = dict( flowgrind_duration = 30,
                          flowgrind_dump     = False,
                          flowgrind_bin      = "flowgrind-wolff",
                          tprofile           = self.testbed_profile,
                          nodetype           = self.node_type )

        # test nodes load from file
        #runs = self.load_pairs_from_file(self.options.pairfile)
        self.runs = [#{'src': int(offset)+1,'dst': int(offset)+2,'run_label': '%s\\\\sra%s' %(int(offset)+1,int(offset)+2)},
                     #{'src': int(offset)+3,'dst': int(offset)+4,'run_label': '%s\\\\sra%s' %(int(offset)+3,int(offset)+4)},
                     #{'src': int(offset)+5,'dst': int(offset)+6,'run_label': '%s\\\\sra%s' %(int(offset)+5,int(offset)+6)},
                     {'src': int(offset)+7,'dst': int(offset)+8,'run_label': '%s\\\\sra%s' %(int(offset)+7,int(offset)+8)}
                    ]

        # repeat loop
        self.iterations  = range(10)

        # parallel or consecutive flows?
        self.parallel    = True

        # inner loop with different scenario settings
        self.scenarios = [ #dict( scenario_label = "Dupthresh 3",flowgrind_cc="reno",flowgrind_opts=["-O","s=TCP_REORDER_MODULE=noreor", "-R", "s=20M"] ),
                           dict( scenario_label = "Linux Native",flowgrind_cc="reno",flowgrind_opts=["-O","s=TCP_REORDER_MODULE=native"] ),
                           dict( scenario_label = "TCP-NCR CF",  flowgrind_cc="reno",flowgrind_opts=["-O","s=TCP_REORDER_MODULE=ncr",    "-O", "s=TCP_REORDER_MODE=1"]),
                           #dict( scenario_label = "TCP-NCR AG",  flowgrind_cc="reno",flowgrind_opts=["-O","s=TCP_REORDER_MODULE=ncr",    "-O", "s=TCP_REORDER_MODE=2"]),
                           dict( scenario_label = "TCP-aNCR CF", flowgrind_cc="reno",flowgrind_opts=["-O","s=TCP_REORDER_MODULE=ancr",   "-O", "s=TCP_REORDER_MODE=1"]),
                           dict( scenario_label = "TCP-aNCR AG", flowgrind_cc="reno",flowgrind_opts=["-O","s=TCP_REORDER_MODULE=ancr",   "-O", "s=TCP_REORDER_MODE=2"]),
                           #dict( scenario_label = "Leung-Ma",    flowgrind_cc="reno",flowgrind_opts=["-O","s=TCP_REORDER_MODULE=leungma","-O", "s=TCP_REORDER_MODE=1"]),
                         ]
