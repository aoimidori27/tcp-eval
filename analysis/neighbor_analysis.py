#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import sys, os, os.path, subprocess, re, time, signal, socket, optparse, time
from logging import info, debug, warn, error
from datetime import timedelta, datetime
from pysqlite2 import dbapi2 as sqlite 

import numpy

# umic-mesh imports
from um_application import Application
from um_config import *
from um_functions import call
from um_analysis.analysis import Analysis

class NeighborAnalysis(Analysis):
    "Application for analysis of neighborhood in regard to ping loss rates"

    def __init__(self):

        Analysis.__init__(self)
        self.parser.set_defaults(outprefix= "neighbors", quality = 100, thruput_thresh = 4.0, 
                                 indir  = "./",
                                 outdir = "./",
                                 digraph=False)
        
        self.parser.add_option('-P', '--prefix', metavar="PREFIX",
                        action = 'store', type = 'string', dest = 'outprefix',
                        help = 'Set prefix of output files [default: %default]')


        self.parser.add_option('-Q', '--quality', metavar="QUAL",
                               action = 'store', type = 'int', dest = 'quality',
                        help = 'Set quality threshold [default: %default]')

        self.parser.add_option("-d", "--digraph",
                               action = "store_true", dest = "digraph",
                               help = "generate a directional graph [default]")

        self.parser.add_option("-T", "--thruput", metavar="THRUPUT",
                               action = 'store', type = 'float', dest = 'thruput_thresh',
                               help = 'Set thruput threshold in Mbit/s [default: %default]')
                               


    def set_option(self):
        "Set options"
        Analysis.set_option(self)

        


    def onLoad(self, record, iterationNo, scenarioNo, test):
        dbcur = self.dbcon.cursor()
    
        recordHeader = record.getHeader()
        run_label = recordHeader["run_label"]


        if test == "flowgrind":
            src = recordHeader["flowgrind_src"]
            dst = recordHeader["flowgrind_dst"]
            
            scenario_label = recordHeader["scenario_label"]
            thruput = record.calculate("thruput")            
            if not thruput:                
                return

            self.found_tput = True

            dbcur.execute("""
                      INSERT INTO tput_tests VALUES (%u, %u, %s, %s, %f, "%s", "%s", "%s")
                      """ % (iterationNo,scenarioNo,src,dst,
                             thruput, run_label, scenario_label, test))

        else:
            src = recordHeader["ping_src"]
            dst = recordHeader["ping_dst"]
        
            pkt_tx = record.calculate("pkt_tx")
            pkt_rx = record.calculate("pkt_rx")
        
            if not pkt_tx:
                return

            self.found_ping = True

            dbcur.execute("""
                          INSERT INTO ping_tests VALUES (%u, %u, %s, %s, %u, %u, "%s")
                          """ % (iterationNo,scenarioNo,src,dst, pkt_tx, pkt_rx, test))

        


    def get_edges(self, test="ping"):

        dbcur = self.dbcon.cursor()
        
        info("Building ping accessibility matrix...")
        
        # get unique pairs and sum up pkt_rx and pkt_tx
        if test == "ping":
            dbcur.execute('SELECT src, dst, SUM(pkt_rx),SUM(pkt_tx) FROM ping_tests GROUP BY src, dst')
        else:
            dbcur.execute('SELECT src, dst, SUM(thruput)/SUM(1) as avg_thruput FROM tput_tests GROUP BY src, dst')
        # nodehash
        nodes = dict()
        edges = dict()

        # indices for directions
        FORWARD = 0
        BACKWARD = 1
        
        for row in dbcur:
            if test == "ping":
                (src,dst,pkt_rx,pkt_tx) = row
                quality = float(pkt_rx) / float(pkt_tx) * 100.
            else:
                (src,dst,quality) = row
            
            if not nodes.has_key(src):
                nodes[src] = src
            if not nodes.has_key(dst):
                nodes[dst] = dst
                
            if src < dst:
                idx = FORWARD
                key = (src, dst)
            else:
                idx = BACKWARD
                key = (dst, src)

            if not edges.has_key(key):
                edges[key] = dict()

            edges[key][idx] = quality

        return (nodes, edges)


    def generate_graph(self, nodes, edges, test, threshold):
        # writing dotfile
        fileprefix = "%s_%s_%.02f" %(self.options.outprefix, test, float(threshold))

        outdir = self.options.outdir
        dotfilename = os.path.join(outdir,fileprefix+".dot")
        pdffilename = os.path.join(outdir,fileprefix+".pdf")
        lstfilename = os.path.join(outdir,fileprefix+".lst")

        info("Generating %s..." %dotfilename)
        dotfile = file(dotfilename, "w")

        if self.options.digraph:
            dotfile.write("digraph ")
        else:
            dotfile.write("graph ")

        # indices for directions
        FORWARD = 0
        BACKWARD = 1
        
        # print header:
        dotfile.write(" neighborhood_%s_%u {\n" % (test, int(threshold)))

        # print nodes
        for node in nodes:
            dotfile.write("n%s [label=%s];\n" %(node,node))


        # print edges
        if self.options.digraph:
            for key,val in edges.iteritems():
                # for each direction one entry
                if val.has_key(FORWARD):
                    quality = val[FORWARD]
                    if quality >= threshold:
                        line = "n%s -> n%s [label=%.1f];\n" %(key[0], key[1], quality)
                        dotfile.write(line)
                if not val.has_key(BACKWARD):
                    continue
                quality = val[BACKWARD]
                if quality >= threshold:
                    line = "n%s -> n%s [label=%.1f];\n" %(key[1],key[0],val[BACKWARD])
                    dotfile.write(line)
        else:
            for key,val in edges.iteritems():

                if not val.has_key(FORWARD):
                    warn("no forward result for %s to %s: ignoring pair" %key)
                    continue
                if not val.has_key(BACKWARD):
                    warn("no backward result for %s to %s: ignoring pair" %key)
                    continue

                # only consider links if both qualities are over threshold and valid
                if val[FORWARD] < threshold or val[BACKWARD] < threshold:
                    continue

                line = 'n%s -- n%s [label="%.1f/%.1f"];\n' %(key[0],key[1],val[FORWARD],val[BACKWARD])
                dotfile.write(line)
                    

        dotfile.write("}\n")

        dotfile.close()

        info("Generating %s ..." %lstfilename)
        lstfile = file(lstfilename, "w")

        for key,val in edges.iteritems():
                if val.has_key(FORWARD) and val[FORWARD] >= threshold:
                    lstfile.write("%s %s\n" %key)
                if val.has_key(BACKWARD) and val[BACKWARD] >= threshold:
                    lstfile.write("%s %s\n" %(key[1],key[0]))

        lstfile.close()


        # generate pdf
        info("Generating %s..." %pdffilename)
        cmd = [ "dot", "-Tpdf", "-o", pdffilename, dotfilename ]
        call(cmd, shell=False)


    def run(self):
        "Main Method"

        # database in memory to access data efficiently
        self.dbcon = sqlite.connect(':memory:')
        dbcur = self.dbcon.cursor()
        dbcur.execute("""
        CREATE TABLE ping_tests (iterationNo INTEGER,
                                 scenarioNo  INTEGER,
                                 src         INTEGER,
                                 dst         INTEGER,
                                 pkt_tx      INTEGER,
                                 pkt_rx      INTEGER,
                                 test        VARCHAR(50))
        """)

        dbcur.execute("""
        CREATE TABLE tput_tests (iterationNo INTEGER,
                                 scenarioNo  INTEGER,
                                 src         INTEGER,
                                 dst         INTEGER,                            
                                 thruput     DOUBLE,
                                 run_label   VARCHAR(70),
                                 scenario_label VARCHAR(70),
                                 test        VARCHAR(50))
        """)
        self.found_ping = False
        self.found_tput = False

        # only load ping,fping and flowgrind test records
        self.loadRecords(tests=["ping","fping","flowgrind"])


        self.dbcon.commit()

        if self.found_ping:
            (nodes, edges) = self.get_edges("ping")
            self.generate_graph(nodes, edges, "ping", self.options.quality)
        if self.found_tput:
            (nodes, edges) = self.get_edges("tput")
            self.generate_graph(nodes, edges, "tput", self.options.thruput_thresh)



            
    def main(self):
        "Main method of the ping stats object"

        self.parse_option()
        self.set_option()
        NeighborAnalysis.run(self)

# this only runs if the module was *not* imported
if __name__ == '__main__':
    NeighborAnalysis().main()

