#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import sys, os, os.path, subprocess, re, time, signal, socket, optparse, time
from logging import info, debug, warn, error
from datetime import timedelta, datetime
from numpy import *
from scipy import *
 
# umic-mesh imports
from um_application import Application
from um_config import *


class Analysis(Application):
    "Framework for UMIC-Mesh analysis"

    def __init__(self):
        
        Application.__init__(self)
        
        # object variables
        self.action = ''
        self.analysis = 'none'
        self.max_hops = 0

        # initialization of the option parser
        usage = "usage: %prog [options] [HOW] WHAT \n" \
                "where  HOW := { min | max | mean | median | deviation | fraction } \n"

        self.parser.set_usage(usage)
        self.parser.set_defaults(nodes = 2, iterations = 1, runs = 1, indir = "./",
                                outdir = "stdout", hop_count = 0, plot = 0)

        self.parser.add_option('-N', '--nodes', metavar="Nodes",
                        action = 'store', type = 'int', dest = 'nodes',
                        help = 'Set range of mrouters covered [default: %default]')
        self.parser.add_option('-I', '--iterations', metavar="Iters",
                        action = 'store', type = 'int', dest = 'iterations',
                        help = 'Set number of tests that were run in a row [default: %default]')
        self.parser.add_option('-R', '--runs', metavar="Run",
                        action = 'store', type = 'int', dest = 'runs',
                        help = 'Set number of test runs that were performed in a row [default: %default]')
        self.parser.add_option('-D', '--input-directory', metavar="InDir",
                        action = 'store', type = 'string', dest = 'indir',
                        help = 'Set directory which contains the measurement results [default: %default]')
        self.parser.add_option('-O', '--output-directory', metavar="OutDir",
                        action = 'store', type = 'string', dest = 'outdir',
                        help = 'Set directory to which the output is given [default: %default]')
        self.parser.add_option('-H', '--hop-count', metavar="HOP",
                        action = 'store', type = 'int', dest = 'hop_count',
                        help = 'Use HOW operations on all nodes (0) or on nodes with '\
                               'same hop count only (1), requires "hops" file [default: %default]')
        self.parser.add_option('-P', '--plot', metavar="PLOT",
                        action = 'store', type = 'int', dest = 'plot',
                        help = 'Create standard (0) or plottable output (1), requires '\
                               '"hops" file and -H 1 option [default: %default]')


    def set_option(self):
        "Set options"
        
        Application.set_option(self)
        
        # correct numbers of arguments?
        if len(self.args) > 0:
            if len(self.args) == 1:
                self.action = self.args[0]
            elif len(self.args) == 2:
                self.analysis = self.args[0]
                self.action = self.args[1]
        else:
            self.parser.error("incorrect number of arguments")

        # does the command exists?
        if not self.analysis in ("min", "max", "mean", "median", "deviation", "none", "fraction"):
            print("I don't know this HOW !")


    def get_stats(self, ReExpr1, ReExpr2):
        "Get statistic depending on two Regular Expressions from measurement files"       
 
        # Define RE's
        ReExpr = re.compile(ReExpr1)
        ReExpr_value = re.compile(ReExpr2)
        
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        
        for source in range(1, self.options.nodes + 1):
            for target in range(1, self.options.nodes + 1):
                if source == target:
                    continue
                failed_trys = 0
                
                for run in range(1, self.options.runs + 1):
                    for iterate in range(1, self.options.iterations + 1):
                        
                        # Open File
                        file_name = "i%02i_smrouter%i_tmrouter%i_r%03i" % (iterate, source, target, run)
                        
                        if os.path.exists("%s%s" %(self.options.indir, file_name)):
                            file = open("%s%s" %(self.options.indir, file_name), "rU")
                        else:
                            print("WARNING: File %s%s does not exist !" %(self.options.indir, file_name))
                            continue

                        output = file.read()
                        debug(output)

                        # Matching
                        match = ReExpr.finditer(output)
                        value = 0
                        counter = 0
                        for result in match:
                            debug(result.group())
                            str_value = ReExpr_value.search(result.group())
                            if str_value:
                                value += float(str_value.group())
                                debug(str_value.group())
                                counter += 1
                            else:
                                failed_trys += 1
                                debug("No matches for Regular Expression %s in file %s" %(ReExpr2, file_name))
                                
                        # Average over all seen values in this file
                        if counter != 0:
                            stats_input[source-1][target-1] += value/counter
                        else:
                            failed_trys += 1
                            debug("No matches for Regular Expression %s in file %s" %(ReExpr1, file_name))
                
                # Array holds summed up values for every run and iteration. Average over all of them 
                stats_input[source-1][target-1] = stats_input[source-1][target-1] / \
                                                    (self.options.runs*self.options.iterations - failed_trys)
        return stats_input


    def get_hop_count(self):
        "Get hop_count matrix out of hops file"

        if os.path.isfile(self.options.indir + "none_hops"):
            FILE = open(self.options.indir + "none_hops" ,"r")
            file_content_list = FILE.readlines()
        else:
            print("Please create 'hops' file first ! \n um_analysis_ping -O 'dir' hops")
            sys.exit(0)

        RegHops = re.compile("\d+")
        
        hop_values = zeros( [self.options.nodes, self.options.nodes], int)
        counterX = 0
        
        for file_content in file_content_list:
            match = RegHops.finditer(file_content)
            counterY = 0
            for result in match:
                if counterX >= self.options.nodes:
                    continue
                else:
                    if counterY >= self.options.nodes:
                        continue
                    else:
                        hop_values[counterX][counterY] = int(result.group())
                    counterY += 1   
            counterX += 1
        
        debug(hop_values)
        self.max_hops = hop_values.max()
        
        return hop_values

    def get_neighs_per_hop(self):
        "Gets the Count of Neighbours per Hop"
        
        hops = self.get_hop_count()
        neighs = zeros([self.options.nodes, self.max_hops], int)
        
        #Get #neighbours per hopcount and node
        for hop in range(1, self.max_hops+1):
            for source in range(1, self.options.nodes+1):
                count_neigh = 0
                for target in range(1, self.options.nodes+1):
                    if hops[source-1][target-1] == hop:
                        count_neigh += 1
                neighs[source-1][hop-1] = count_neigh
        
        return neighs

    def inline_stats(self, array, hops):
        "Get the values for a specific hop count"

        counter = 0
        length = (self.options.nodes - 1) * self.options.nodes

        if self.options.hop_count == 0:
            inline_stats = zeros(length, float)
            for source in range(1, self.options.nodes + 1):
                for target in range(1, self.options.nodes + 1):
                        if source == target:
                            continue
                        inline_stats[counter]=array[source-1][target-1]
                        counter +=1
        else:
            hop_count = self.get_hop_count()
            inline_stats = zeros(length, float)
            inline_stats.fill(-1)
            for source in range(1, self.options.nodes + 1):
                for target in range(1, self.options.nodes + 1):
                        if source == target:
                            continue
                            
                        if hop_count[source-1][target-1] == hops and hop_count[source-1][target-1] != 0:
                            debug("source:%i, target:%i\n" %(source-1, target-1))
                            inline_stats[counter]=array[source-1][target-1]
                            counter +=1
                            
            # Filter those elements that were not set
            mask_array = where(inline_stats >= 0,1,0)
            inline_stats = compress(mask_array, inline_stats)

        debug(inline_stats)
        
        return inline_stats


    def min(self, array, hops):
        "Calculates the Minimum of seen values"        

        print("Min:")
        result = self.inline_stats(array, hops)
        
        return result.min()

    
    def max(self, array, hops):
        "Calculates the Maximum of seen values"        

        print("Max:")
        result = self.inline_stats(array, hops)
        
        return result.max()


    def mean(self, array, hops):
        "Calculates the Mean of seen values"        

        print("Mean:")
        result = self.inline_stats(array, hops)
        
        return result.mean()


    def median(self, array, hops):
        "Calculates the Median of seen values"        

        print("Median:")
        result = self.inline_stats(array, hops)
        
        return median(result)


    def deviation(self, array, hops):
        "Calculates the deviation of seen values"        

        print("Deviation:")
        result = self.inline_stats(array, hops)
        
        return result.std()
    
    def fraction(self, array, hops):
        "Calculates the cumulative fraction of nodes on seen values"        

        if self.options.hop_count == 1:
            if self.options.outdir == "stdout":
                print("Use only with -O. You can't see nothing on the screen :)")
            else:
                for hop in range(1, self.max_hops+1):
                    filename = self.analysis + "_" + self.action + "_values_" + str(hop)
                    print("Creating GnuPlot file %s%s" %(self.options.outdir,filename))
                    file = self.options.outdir + filename
                    if os.path.isfile(file):
                        os.remove(file)
                    FILE = open(file,"a")
                    FILE.write("#Fraction\t#%s\n" %self.action)
                    FILE.close()
#                    filename = self.analysis + "_" + self.action + "_values"

                    result = self.inline_stats(array, hop)
                    result_sort = sort(result)
                    array_len = len(result_sort)
        
                    for value in result_sort:
                        count = 0
                        for result_count in range(0, array_len):
                            if result[result_count] <= value:
                                count += 1
                        fraction = float(count) / float(array_len)
        
                        if self.options.outdir == "stdout":
                            print("%s\t%s" %(fraction, value))
                        else:
                            print("Appending values to GnuPlot file %s%s\n" %(self.options.outdir,filename))
                            file = self.options.outdir + filename
                            FILE = open(file,"a")
                            FILE.write("%s\t%s\n" %(fraction, value))
                            FILE.close()
        else:
            result = self.inline_stats(array, -1)
            array_len = len(result)

            if self.options.outdir == "stdout":
                print("#Fraction\t#%s" %self.action)
            else:
                filename = self.analysis + "_" + self.action + "_values"
                print("Creating GnuPlot file %s%s" %(self.options.outdir,filename))
                file = self.options.outdir + filename
                if os.path.isfile(file):
                    os.remove(file)
                FILE = open(file,"a")
                FILE.write("#Fraction\t#%s\n" %self.action)
                FILE.close()
                
    #        for value in range(0, int(result.max() + 1.5)):
            result_sort = sort(result)
            for value in result_sort:
                count = 0
                for result_count in range(0, array_len):
                    if result[result_count] <= value:
                        count += 1
                fraction = float(count) / float(array_len)
                if self.options.outdir == "stdout":
                    print("%s\t%s" %(fraction, value))
                else:
                    filename = self.analysis + "_" + self.action + "_values"
                    print("Appending values to GnuPlot file %s%s\n" %(self.options.outdir,filename))
                    file = self.options.outdir + filename
                    FILE = open(file,"a")
                    FILE.write("%s\t%s\n" %(fraction, value))
                    FILE.close()
        sys.exit(0)


    def none(self, array, hops):
        "Returns just the seen values"        

        print("Doing nothing do parsed values ...")
        if hops == -1:
            return array
        else:
            result = self.inline_stats(array, hops)
            return result


    def conf_interval(self, inlined_stats):
        "Calculates 0.95 confidence intervall"    

        #0.95 confidence interval
        return 1.96 * inlined_stats.std() / sqrt(len(inlined_stats))


    def print_out(self, stats, hops, interval, hop_count):
        "Prints out the calculated results"

        if self.options.outdir == "stdout":
            if hops == -1:
                print(stats)
            elif self.options.plot == 1:
                print("%s\t%s\t%s\t%s" %(hops, stats, interval, hop_count))
            else:
                print("For %s hop(s):" %hops)
                print(stats)
        else:
            if hops == -1:
                filename = self.analysis + "_" + self.action
                print("Writing values to file %s%s" %(self.options.outdir,filename))
                file = self.options.outdir + filename
                FILE = open(file,"w")
                
                # Special handling for hops file because of new line failure with > 18 nodes
                if self.action == "hops":
                    for source in range(1, self.options.nodes + 1):
                        for target in range(1, self.options.nodes + 1):
                                if source == target:
                                    FILE.write("0\t")
                                else:
                                    FILE.write("%i\t" %int(stats[source-1][target-1]))
                        FILE.write("\n")
                else:
                    FILE.write(str(stats))

                FILE.close()
            
            elif self.options.plot == 1:
                #create plottable output
                filename = self.analysis + "_" + self.action + "_values"
                print("For %s hop(s):" %hops)
                print("Appending values to GnuPlot file %s%s\n" %(self.options.outdir,filename))
                file = self.options.outdir + filename
                FILE = open(file,"a")
                FILE.write("%s\t%s\t%s\t%s\n" %(hops, stats, interval, hop_count))
                FILE.close()
            
            else:
                filename = self.analysis + "_" + self.action
                print("Appending values to file %s%s" %(self.options.outdir,filename))
                file = self.options.outdir + filename
                FILE = open(file,"a")
                FILE.write("For %s hop(s): \n" %hops)
                FILE.write(str(stats)+"\n")
                FILE.close()


    def run(self):
        "Main Method"
    
        print("Starting processing ...")
        if self.options.hop_count == 1:
            # call the corresponding parse stats method
            result = eval("self.%s()" %(self.action))
            # hop processing
            hop_count = self.get_hop_count()
 
            if self.options.plot == 1:
                if self.options.outdir == "stdout":
                    print("#hops\t#%s_%s\t#intervall\t#hop_count\n" %(self.analysis, self.action))
                else:
                    filename = self.analysis + "_" + self.action + "_values"
                    print("Creating GnuPlot file %s%s" %(self.options.outdir,filename))
                    file = self.options.outdir + filename
                    if os.path.isfile(file):
                        os.remove(file)
                    FILE = open(file,"a")
                    FILE.write("#hops\t#%s_%s\t#conf_intervall_constant\t#hop_count\n" %(self.analysis, self.action))
                    FILE.close()
            else:
                filename = self.analysis + "_" + self.action
                file = self.options.outdir + filename
                if os.path.isfile(file):
                    os.remove(file)

            for hop in range(1, self.max_hops + 1):
                # evaluate for every hop value
                stats = eval("self.%s(%s,%s)" %(self.analysis, "result", "hop"))
                inlined_values = self.inline_stats(result, hop)
                self.print_out(stats, hop, self.conf_interval(inlined_values), len(inlined_values))
        else:
            if self.options.plot == 1:
                print("Please use also the -H option !")
                sys.exit(0)
            
            # call the corresponding parse stats method
            result = eval("self.%s()" %(self.action))
            
            # call the corresponding evaluate stats method
            stats = eval("self.%s(%s,-1)" %(self.analysis, "result"))
            
            # print out the stuff
            self.print_out(stats, -1, 0,-1)
