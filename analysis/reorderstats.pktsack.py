#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

# Script to plot ping output with gnuplot.
#
# Copyright (C) 2007 Arnd Hannemann <arnd@arndnet.de>
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.

# python imports
import dpkt
import struct
import socket
from logging import info, debug, warn, error
from collections import deque

# umic-mesh imports
from um_application import Application

class Info:
    connections = list()

    # check if connection exists
    def check(self, c):
        for entry in Info.connections:
            if Info.compare(self,entry,c) == 1:
                return entry
        return None

    # find the other half connection
    def findOtherHalf(self, c):
        for entry in Info.connections:
            if Info.compare(self,entry,c) == 2:
                return entry
        return None

    # compare two connections
    def compare(self, c1, c2):
       if ((c1['src'] == c2['dst']) and (c1['dst'] == c2['src']) \
          and (c1['sport'] == c2['dport']) and (c1['dport'] == c2['sport'])):
            return 2

       if ((c1['src'] == c2['src']) and (c1['dst'] == c2['dst']) \
          and (c1['sport'] == c2['sport']) and (c1['dport'] == c2['dport'])):
            return 1
       else:
            return 0

    def process(self,file):
        packets = dpkt.pcap.Reader(open(file,'rb'))

        for ts, buf in packets:
            ip_hdr = dpkt.sll.SLL(buf).data

            try:
                tcp_hdr = ip_hdr.data
            except:
                continue

            # ---- set vars ----
            ip_len = ip_hdr.len
            ack = tcp_hdr.ack
            seq = int(tcp_hdr.seq)
            offset = tcp_hdr._get_off()

            flags = [0,0,0,0,0,0]
            hdr_flags = tcp_hdr.flags
            for t in reversed(range(6)):
                flags[t] = hdr_flags % 2
                hdr_flags = hdr_flags/2

            # general connection infos
            c = dict()
            c['src'] = socket.inet_ntoa(ip_hdr.src)
            c['dst'] = socket.inet_ntoa(ip_hdr.dst)
            c['sport'] = tcp_hdr.sport
            c['dport'] = tcp_hdr.dport

            # check if connection is already recorded
            entry = Info.check(self,c)
            half = None
            if entry:
                if not entry.has_key('half'):
                    half = Info.findOtherHalf(self, c)
                    entry['half'] = half
                else:
                    half = entry['half']

            carries_data = 0
            #TODO: - 4 ?
            if ip_len - 40 - offset - 4 > 0:
                carries_data = 1

            # get sack blocks from the tcp options field
            opt = dpkt.tcp.parse_opts(tcp_hdr.opts)
            sack_list = []
            for i in opt:
                if i[0] == 5:
                    oval = i[1]
                    oname, ofmt = ("SAck","!")
                    ofmt += "%iI" % (len(oval)/4)
                    if ofmt and struct.calcsize(ofmt) == len(oval):
                        oval = struct.unpack(ofmt, oval)
                        if len(oval) == 1:
                            oval = oval[0]
                    sack_list.append((oname, oval))
            tcp_hdr.options = sack_list

            # check for sack blocks in this packet
            sack = 0
            dsack = 0
            sack_blocks = []
            try:
                    #save sack blocks for later use
                    sack_blocks = tcp_hdr.options[0][1]

                    sack = 1

                    #dsack detection
                    if ack >= sack_blocks[1]: #1st sack block, right edge
                        dsack = 1
                    if ack <= sack_blocks[0] and len(sack_blocks) >= 3 \
                     and (sack_blocks[0] >= sack_blocks[2] and sack_blocks[1] <= sack_blocks[3]): #ex 2nd sack block, 1st sack block is covered by 2nd
                        dsack = 1

            except:
                pass


            # ---- process connection ---

            # 'sack': record how much packets contained sack blocks
            # 'dsack': number of dsacks
            # 'all':  number of packets for this connection
            # 'high': highest seq nr
            # 'pkts': seq numbers of packets with bools for sacked and rexmit [seq,sacked,rexmitted]
            # 'acked': last ack received
            # 'reorder': number of detected reorderings
            # 'dreorder': detected reorderings with dsack
            # 'syn': seen a syn
            # 'rst': seen a rst
            # 'fin': seen a fin

            if entry == None: # new connection
                c['sack'] = sack
                c['dsack'] = dsack
                c['all'] = 1
                if carries_data:
                    c['high'] = seq
                else:
                    c['high'] = 0
                c['pkts'] = dict()
                c['rexmit'] = deque()
                c['acked'] = ack
                c['reorder'] = 0
                c['dreorder'] = 0
                c['rst'] = 0
                c['fin'] = 0
                c['syn'] = 0
                if flags[4]:
                    c['syn'] = 1
                #for block in range(0, len(sack_blocks), 2):
                #    c['sblocks'].append([sack_blocks[block],sack_blocks[block+1]])
                Info.connections.append(c)

            else: # found old connection
                entry['sack'] += sack
                entry['dsack'] += dsack
                entry['all'] += 1

                half_pkts = None
                entry_pkts = entry['pkts']

                if half:
                    half_pkts = half['pkts']
                    # check if reorder can be detected with acked sack holes
                    if ack > entry['acked']:
                        sacked = 0
                        count = 0
                        for pkt in half_pkts.items():
                            if ack > pkt[0] and pkt[0] >= entry['acked']:
                                if pkt[1][0] == 0 and pkt[1][1] == 0: #neither sacked nor rexmitted
                                    count += 1
                                if pkt[1][0] == 1:
                                    sacked = 1

                        if sacked == 1:
                            half['reorder'] += count

                        # update last acked packet (snd.una)
                        entry['acked'] = ack

                    #dsack reordering detection
                    if dsack == 1:
                        if sack_blocks[0] in half['rexmit']: #dsack acks a retransmitted segment
                            half['dreorder'] += 1
                        else:
                            pass #TODO: packet duplication


                    if half_pkts:
                        half_keys = half_pkts.keys()
                        half_keys.sort()
                        sacked = 0
                        new_sacked = 0
                        for key in half_keys:
                            #remove pkts with seq lower than acked
                            if key < entry['acked']:
                                if half_pkts[key][1] == 1: #pkt was retransmitted
                                  half['rexmit'].append(key)
                                del half_pkts[key]
                                continue

                            if half_pkts[key][0] == 1: #already sacked
                                if sacked == 1 and new_sacked > 0:
                                    half['reorder'] += new_sacked
                                    new_sacked = 0
                                else:
                                    sacked = 1
                                continue
                            #process sack blocks
                            for block in range(0, len(sack_blocks), 2):
                                if key >= sack_blocks[block] and key < sack_blocks[block+1]:
                                    half_pkts[key][0] = 1 #sacked
                                    if half_pkts[key][1] == 0: #not rexmitted
                                        new_sacked += 1
                                    break


                if carries_data:
                    #store packet if not already there
                    if not entry_pkts.has_key(seq):
                        entry_pkts[seq] = [0,0]
                    #store highest sent seq no
                    if seq > entry['high']:
                        entry['high'] = seq
                    else: #paket is retransmit
                        if entry_pkts.has_key(seq):
                            entry_pkts[seq][1] = 1

                if flags[3]:
                    entry['rst'] = 1
                if flags[5]:
                    entry['fin'] = 1


class ReorderInfo(Application):
    def __init__(self):
        Application.__init__(self)

        # initialization of the option parser
        usage = "usage: %prog <Pcap file>\nOutput: infos about reordering"
        self.parser.set_usage(usage)
        #self.parser.set_defaults(opt1 = Bool, opt2 = 'str')

        #self.parser.add_option("-s", "--long", metavar = "VAR",
        #                       action = "store", dest = "var",
        #                       help = "Help text to be shown [default: %default]")

    def set_option(self):
        """Set the options"""

        Application.set_option(self)

        if len(self.args) == 0:
            error("Pcap file must be given!")
            sys.exit(1)


    def run(self):
        info = Info()
        info.process(self.args[0])

        print "Src\t\tsport\tDst\t\tdport\tSyn Rst Fin\tSack\tDSack\tPkts\treor\tdreor\t% reor"
        con_reordered = 0
        pkt_reordered = 0
        pkt_all = 0
        for con in info.connections:
            if con['reorder'] > 0 or con['dreorder'] > 0:
                con_reordered += 1
            pkt_reordered += con['reorder'] + con['dreorder']
            pkt_all += con['all']
            print "%s\t%s\t%s\t%s\t  %s   %s   %s\t%s\t%s\t%s\t%s\t%s\t%f" %(con['src'],con['sport'],con['dst'],con['dport'],\
                                                       con['syn'],con['rst'],con['fin'],con['sack'],con['dsack'],\
                                                       con['all'],con['reorder'],con['dreorder'],float(con['reorder']+con['dreorder'])/con['all']*100)
        print "No. connections with reordering: %u out of %u (%f%%)" %(con_reordered, len(info.connections), float(con_reordered)/len(info.connections)*100)
        print "Packets reordered: %u out of %u (%f%%)" %(pkt_reordered, pkt_all, float(pkt_reordered)/pkt_all*100)


    def main(self):
        self.parse_option()
        self.set_option()
        self.run()



if __name__ == "__main__":
    ReorderInfo().main()

