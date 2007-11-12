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
from um_analysis.testrecords import TestRecordFactory
from um_analysis.analysis import Analysis

class NeighborAnalysis(Analysis):
    "Application for analysis of neighborhood in regard to ping loss rates"

    def __init__(self):

        Analysis.__init__(self)
        self.parser.set_defaults(outprefix= "neighbors", quality = 100,
                                 indir  = "./",
                                 outdir = "./",
                                 digraph=False);
        
        self.parser.add_option('-P', '--prefix', metavar="PREFIX",
                        action = 'store', type = 'string', dest = 'outprefix',
                        help = 'Set prefix of output files [default: %default]')


        self.parser.add_option('-Q', '--quality', metavar="QUAL",
                               action = 'store', type = 'int', dest = 'quality',
                        help = 'Set quality threshold [default: %default]')

        self.parser.add_option("-d", "--digraph",
                               action = "store_true", dest = "digraph",
                               help = "generate a directional graph [default]")



    def set_option(self):
        "Set options"
        Analysis.set_option(self)


    def onLoad(self, record, iterationNo, scenarioNo, test):
        dbcur = self.dbcon.cursor()
    
        recordHeader = record.getHeader()
        src = recordHeader["ping_src"]
        dst = recordHeader["ping_dst"]
        
        pkt_tx = record.calculate("pkt_tx")
        pkt_rx = record.calculate("pkt_rx")        

        dbcur.execute("""
                      INSERT INTO tests VALUES (%u, %u, %s, %s, %u, %u, "%s")
                      """ % (iterationNo,scenarioNo,src,dst, pkt_tx, pkt_rx, test))

        


    def run(self):
        "Main Method"

        # database in memory to access data efficiently
        self.dbcon = sqlite.connect(':memory:')
        dbcur = self.dbcon.cursor()
        dbcur.execute("""
        CREATE TABLE tests (iterationNo INTEGER,
                            scenarioNo  INTEGER,
                            src         INTEGER,
                            dst         INTEGER,
                            pkt_tx      INTEGER,
                            pkt_rx      INTEGER,
                            test        VARCHAR(50))
        """)

        # only load ping test records
        self.loadRecords(tests=["ping"])

        self.dbcon.commit()
                
        
        info("Building accessibility matrix...")
        
        # get unique pairs and sum up pkt_rx and pkt_tx
        dbcur.execute('SELECT src, dst, SUM(pkt_rx),SUM(pkt_tx) FROM tests GROUP BY src, dst')

        # nodehash
        nodes = dict()
        edges = dict()

        # indices for directions
        FORWARD = 0
        BACKWARD = 1
        
        for row in dbcur:
            (src,dst,pkt_rx,pkt_tx) = row

            
            if not nodes.has_key(src):
                nodes[src] = src
            if not nodes.has_key(dst):
                nodes[dst] = dst
            quality = float(pkt_rx) / float(pkt_tx) * 100.

            if src < dst:
                idx = FORWARD
                key = (src, dst)
            else:
                idx = BACKWARD
                key = (dst, src)

            if not edges.has_key(key):
                edges[key] = dict()

            edges[key][idx] = quality
            
#            if  quality >= self.options.quality:
#                edges.append("n%s -> n%s [label=%.1f];" %(src,dst,quality))

        # writing dotfile
        fileprefix = "%s_%u" %(self.options.outprefix, self.options.quality)

        dotfilename = fileprefix+".dot"
        pdffilename = fileprefix+".pdf"
        info("Generating %s..." %dotfilename)
        dotfile = file(dotfilename, "w")

        if self.options.digraph:
            dotfile.write("digraph ")
        else:
            dotfile.write("graph ")
        
        # print header:
        dotfile.write(" neighborhood_quality%u {\n" % self.options.quality)

        # print nodes
        for node in nodes:
            dotfile.write("n%s [label=%s];\n" %(node,node))

        threshold = self.options.quality

        # print edges
        if self.options.digraph:
            for key,val in edges.iteritems():
                
                # for each direction one entry
                quality = val[FORWARD]
                if quality >= threshold:
                    line = "n%s -> n%s [label=%.1f];\n" %(key[0],key[1],quality)
                    dotfile.write(line)
                quality = val[BACKWARD]
                if quality >= threshold:
                    line = "n%s -> n%s [label=%.1f];\n" %(key[1],key[0],val[BACKWARD])
                    dotfile.write(line)
        else:
            for key,val in edges.iteritems():
                # only consider links if both qualities are over threshold
                if val[FORWARD] < threshold or val[BACKWARD] < threshold:
                    continue

                line = 'n%s -- n%s [label="%.1f/%.1f"];\n' %(key[0],key[1],val[FORWARD],val[BACKWARD])
                dotfile.write(line)
                    

        dotfile.write("}\n")

        dotfile.close()

        # generate pdf
        info("Generating %s..." %pdffilename)
        cmd = [ "dot", "-Tpdf", "-o", pdffilename, dotfilename ]
        call(cmd, shell=False)


            
    def main(self):
        "Main method of the ping stats object"

        self.parse_option()
        self.set_option()
        NeighborAnalysis.run(self)

# this only runs if the module was *not* imported
if __name__ == '__main__':
    NeighborAnalysis().main()

