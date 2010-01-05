#!/usr/bin/python

import dpkt
import struct
import socket

from logging import info, debug, warn, error

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


    def addConnection(self,ip_hdr):
        try:
            tcp_hdr = ip_hdr.data
        except:
            return

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
        # 'rexmit': seq numbers of retransmitted segments
        # 'acked': last ack received
        # 'reorder': number of detected reorderings
        # 'dreorder': detected reorderings with dsack
        # 'sblocks': sack score board
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
            c['rexmit'] = dict()
            c['acked'] = ack
            c['reorder'] = 0
            c['dreorder'] = 0
            c['sblocks'] = []
            #c['old_sack'] = []
            c['rst'] = 0
            c['fin'] = 0
            c['syn'] = 0
            if flags[4]:
                c['syn'] = 1
            for block in range(0, len(sack_blocks), 2):
                c['sblocks'].append([sack_blocks[block],sack_blocks[block+1]])
            Info.connections.append(c)

        else: # found old connection
            entry['sack'] += sack
            entry['dsack'] += dsack
            entry['all'] += 1

            if entry and half:
                # check if reorder can be detected with acked sack holes
                if entry['sblocks'] != []:

                    if ack > entry['acked']:
                        #create list of holes
                        holes = []
                        if ack >= entry['sblocks'][0][0]:
                            if entry['acked'] < entry['sblocks'][0][0]:
                                holes.append([entry['acked'], entry['sblocks'][0][0]])

                        for block in range(len(entry['sblocks'])-1):
                            if entry['sblocks'][block+1][0] <= ack:
                                holes.append([entry['sblocks'][block][1], entry['sblocks'][block+1][0]])

                        if ack == entry['high']:
                            if entry['high'] > entry['sblocks'][len(entry['sblocks'])-1][1]:
                                holes.append([entry['sblocks'][len(entry['sblocks'])-1][1], entry['high']])

                        #find sack_hole for ack
                        for hole in holes:
                            while hole[0] != hole[1]:
                                if not half['rexmit'].has_key(hole[0]):
                                    #first packet in hole hasn't been retransmitted -> whole hole is reordered
                                    half['reorder'] += 1
                                    break
                                else:
                                    #first packet was retransmitted, add packet length and check again for new hole
                                    hole[0] += half['rexmit'][hole[0]]

                #dsack reordering detection
                if dsack == 1:
                    if half['rexmit'].has_key(sack_blocks[0]): #dsack acks a retransmitted segment
                        half['dreorder'] += 1
                    else:
                        pass #TODO: packet duplication
                        #dsack_done = 0
                        #for sb in entry['sblocks']:
                        #    if sack_blocks[0] >= sb[0] and sack_blocks[1] <= sb[1]: #dsack was sacked before
                        #        half['dreorder'] += 1
                        #        dsack_done = 1
                        #        break
                        #for sb in entry['old_sack']:
                        #    if sack_blocks[0] >= sb[0] and sack_blocks[1] <= sb[1]: #dsack was sacked before
                        #        half['dreorder'] += 1
                        #        break

            #process sack blocks
            #also includes reordering detection for sack holes closed bei sack blocks
            if len(entry['sblocks']) > 0:

                #delete sack blocks, which are lower than cumulative ack
                for block in entry['sblocks']:
                    if block[1] <= ack:
                        #entry['old_sack'].append(block) #save old sack blocks for dsack reordering detection
                        entry['sblocks'].remove(block)
                        break

                #merge with new sack blocks
                for block in range(0, len(sack_blocks), 2):
                    done = 0
                    for i in range(len(entry['sblocks'])):
                        #sack block exists
                        if sack_blocks[block] == entry['sblocks'][i][0] and sack_blocks[block+1] == entry['sblocks'][i][1]:
                            done = 1
                            break

                        #new sack block is longer than existing
                        elif sack_blocks[block] == entry['sblocks'][i][0] and sack_blocks[block+1] > entry['sblocks'][i][1]:
                            save_hole = entry['sblocks'][i][1]
                            entry['sblocks'][i][1] = sack_blocks[block+1]

                            if len(entry['sblocks']) > i+1:
                                if entry['sblocks'][i+1][1] == sack_blocks[block+1]:
                                    #sack hole closed
                                    entry['sblocks'].remove(entry['sblocks'][i+1])
                                    if not half['rexmit'].has_key(save_hole):
                                        #reordering
                                        if half:
                                            half['reorder'] += 1

                            done = 1
                            break


                    if not done:
                        entry['sblocks'].append([sack_blocks[block],sack_blocks[block+1]])
            else:
                for block in range(0, len(sack_blocks), 2):
                    entry['sblocks'].append([sack_blocks[block],sack_blocks[block+1]])

            # updated last acked packet (snd.una)
            if ack > entry['acked']:
                entry['acked'] = ack

            if carries_data:
                if seq > entry['high']:
                    #store highest sent seq no
                    entry['high'] = seq
                else: #paket is retransmit, store seq no and length
                    entry['rexmit'][seq] = ip_len - 40 - offset - 4

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

        self.packets = dpkt.pcap.Reader(open(self.args[0],'rb'))
#        count = 1
#        count2 = 0
        for ts, buf in self.packets:
            eth = dpkt.sll.SLL(buf)
            info.addConnection(eth.data)
#            count += 1
#            if count == 1000:
#                count2 += 1
                #print count2
#                count = 0

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
                                                       con['all'],con['reorder'],con['dreorder'],float(con['reorder']+con['dreorder'])/con['all'])
        print "No. connections with reordering: %u out of %u (%f)" %(con_reordered, len(info.connections), float(con_reordered)/len(info.connections))
        print "Packets reordered: %u out of %u (%f)" %(pkt_reordered, pkt_all, float(pkt_reordered)/pkt_all)


    def main(self):
        self.parse_option()
        self.set_option()
        self.run()



if __name__ == "__main__":
    ReorderInfo().main()

