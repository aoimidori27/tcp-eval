#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import subprocess, re
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_config import *
from um_functions import *


class Madwifi(Application):
    "Class to handle madwifi-ng"


    def __init__(self, devicename = 'ath0'):
        "Constructor of the object"
    
        Application.__init__(self)
        
        # object variables
        self.commands = ('loadmod', 'unloadmod', 'createdev', 'killdev',
                         'ifup', 'ifdown', 'setessid', 'setchannel', 
                         'settxpower', 'setantenna', 'start')
        self.action = ''
    
        nodeinfo  = getnodeinfo()
        nodenr    = getnodenr().__str__()
        meshdevs  = nodeinfo['meshdevices']
        devicecfg = meshdevs[devicename]
        activecfg = deviceconfig[devicecfg]
            
        # initialization of the option parser
        usage = "usage: %prog [options] COMMAND \n" \
                "where  COMMAND := { loadmod | unloadmod | createdev | " \
                "killdev | ifup | ifdown | \n" \
                "                    setessid | setchannel | " \
                "settxpower | setantenna | start }"
        self.parser.set_usage(usage)
        self.parser.set_defaults(device   = devicename,
                                 address  = re.sub('@NODENR', nodenr,  activecfg['address']),
                                 channel  = activecfg['channel'],
                                 essid    = activecfg['essid'],
                                 wlanmode = activecfg['wlanmode'],
                                 hwdevice = activecfg['hwdevice'],
                                 txpower  = activecfg['txpower'],
                                 antenna  = activecfg['antenna'])
        
        self.parser.add_option("-a", "--addr", metavar = "IP",
                               action = "store", dest = "address",
                               help = "define the IP address [default: %default]")                
        self.parser.add_option("-c", "--chan", metavar = "NUM", type = int,
                               action = "store", dest = "channel",
                               help = "define the wireless channel [default: %default]")
        self.parser.add_option("-d", "--dev",  metavar = "DEV",
                               action = "store", dest = "device",
                               help = "define the device [default: %default]")  
        self.parser.add_option("-e", "--essid", metavar = "ID",
                               action = "store", dest = "essid",
                               help = "define the essid [default: %default]")
        self.parser.add_option("-m", "--mode", metavar = "MODE",
                               action = "store", dest = "wlanmode",
                               help = "define the mode [sta|adhoc|ap|monitor|wds|"\
                               "ahdemo] \n [default: %default]")
        self.parser.add_option("-w", "--hwdev", metavar = "HW",
                               action = "store", dest = "hwdevice",
                               help = "define the device [default: %default]")
        self.parser.add_option("-t", "--txpower", metavar = "TX", type = int,
                               action = "store", dest = "txpower",
                               help = "define the TX-Power [default: %default]")
        self.parser.add_option("-z", "--ant", metavar = "ANT", type = int,
                               action = "store", dest = "antenna",
                               help = "define antenna for transmit and receive"\
                               "\n [default: %default]")
   
   
    def set_option(self):
        "Set options"
        
        Application.set_option(self)
        
        # correct numbers of arguments?
        if len(self.args) != 1:
            self.parser.error("incorrect number of arguments")

        # set arguments
        self.action = self.args[0]

        # does the command exists?
        if not self.action in self.commands:
            self.parser.error("unknown COMMAND %s" %(self.action))
    

    def loadmod(self):
        "Loading madwifi-ng driver"

        prog1 = subprocess.Popen(["lsmod"], stdout = subprocess.PIPE)
        prog2 = subprocess.Popen(["grep", "ath_pci"],
                                 stdin = prog1.stdout, stdout = subprocess.PIPE)
        (stdout, stderr) = prog2.communicate()
    
        if stdout == "":
            info("Loading madwifi-ng driver...")
            try:
                call(["modprobe", "ath-pci", "autocreate=none"],
                     shell = False)
            except CommandFailed:
                error("Loading madwifi-ng driver was unsuccessful")
                sys.exit(-1)
        else:
            warn("Madwifi-ng is already loaded")

    
    def unloadmod(self):
        "Loading madwifi-ng driver"

        prog1 = subprocess.Popen(["lsmod"], stdout = subprocess.PIPE)
        prog2 = subprocess.Popen(["grep", "ath-pci"], 
                                 stdin = prog1.stdout, stdout = subprocess.PIPE)
        (stdout, stderr) = prog2.communicate()

        if not stdout == "":
            info("Unloading madwifi-ng")
            retcode = subprocess.call(["rmmod", "ath-pci wlan-scan-sta " \
                                       "ath-rate-sample wlan ath-hal"], \
                                      shell = True)
            if retcode < 0:
                error("Unloading madwifi-ng driver was unsuccessful")
                sys.exit(-1)
        else:
            warn("Madwifi-ng is not loaded")


    def createdev(self):
        "Creating VAP in the desired mode"
    
        info("Creating VAP in %s mode" %(self.options.wlanmode))
        cmd = ("wlanconfig", self.options.device, "create", "wlandev", \
               self.options.hwdevice, "wlanmode", self.options.wlanmode)
        info(cmd)
        try:
            stderr = execute(cmd, shell = False)[1]
        except CommandFailed:
            error("Creating %s was unsuccessful" % self.options.device)
            sys.exit(-1)


    def killdev(self):
        "Destroying VAP"

        if self.deviceexists():
            info("Destroying VAP %s" %(self.options.device))
            try:
                call(["wlanconfig", self.options.device, "destroy"], \
                     shell = False)
            except CommandFailed:
                error("Destroying VAP %s was unsuccessful" %(self.options.device))
                sys.exit(-1)
        else:
            warn("VAP %s does not exist" %(self.options.device))


    def ifup(self):
        "Bring the network interface up"

        if self.deviceexists():
            info("Bring VAP %s up" %(self.options.device))
            try:
                call(["ip", "link", "set", self.options.device, "up"], \
                     shell = False)
                call(["ip", "addr", "flush", "dev", self.options.device],
                     shell = False)
                call(["ip", "addr", "add", self.options.address, "dev", self.options.device],
                     shell = False)
            except CommandFailed:
                error("Bring VAP %s up was unsuccessful" %(self.options.device))
                sys.exit(-1)
        else:
            warn("VAP %s does not exist" %(self.options.device))


    def ifdown(self):
        "Take a network interface down"

        if self.deviceexists():
            info("Take VAP %s down" %(self.options.device))
            try:
                call(["ip", "link", "set", self.options.device, "down"], 
                     shell = False)
                call(["ip", "addr", "flush", "dev", self.options.device],
                     shell = False)
            except CommandFailed:
                error("Take VAP %s down was unsuccessful" %(self.options.device))
                sys.exit(-1)
        else:
            warn("VAP %s does not exist" %(self.options.device))
        
    
    def setessid(self):
        "Set the ESSID of desired device"

        if self.deviceexists():
            info("Setting essid on %s to %s" %(self.options.device, self.options.essid))
            try:
                call(["iwconfig", self.options.device, "essid", self.options.essid],
                     shell = False)
            except CommandFailed:
                error("Setting essid on %s to %s was unsuccessful" \
                      %(self.options.device, self.options.essid))
                sys.exit(-1)
        else:
            warn("VAP %s does not exist" %(self.options.device))
    
        
    def setchannel(self):
        "Set the WLAN channel of desired device"

        if self.deviceexists():
            info("Setting channel on %s to %d" %(self.options.device, self.options.channel))
            try:
                call(["iwconfig", self.options.device, "channel", self.options.channel.__str__()],
                     shell = False)
            except CommandFailed:
                error("Setting channel on %s to %d was unsuccessful" \
                      %(self.options.device, self.options.channel))
                sys.exit(-1)
        else:
            warn("VAP %s does not exist" %(self.options.device))
        

    def settxpower(self):
        "Set the TX-Power of desired device"

        if self.deviceexists():
            info("Setting txpower on %s to %s dBm" %(self.options.device, self.options.txpower))
            try:
                call(["iwconfig", self.options.device, "txpower",
                      self.options.txpower.__str__()], shell = False)
            except CommandFailed:
                error("Setting txpower on %s to %s dBm was unsuccessful"
                      %(self.options.device, self.options.txpower))
                sys.exit(-1)
        else:
            warn("VAP %s does not exist" %(self.options.device))


    def setantenna(self):
        "Set the antenna of desired device"

        try:
            info("Setting tx/rx-antenna to %d" % self.options.antenna)
            call("echo 0 > /proc/sys/dev/%s/diversity" % (self.options.hwdevice),
                 shell = True)
            call("echo %d > /proc/sys/dev/%s/txantenna" % (self.options.antenna, self.options.hwdevice),
                 shell = True)
            call("echo %d > /proc/sys/dev/%s/rxantenna" % (self.options.antenna, self.options.hwdevice),
                 shell = True)
        except CommandFailed:
            error("Setting tx/rx-antenna to %d was unsuccessful" % self.options.antenna)
            sys.exit(-1)
   
 
    def deviceexists(self):
        cmd = ("ip", "link", "show",self.options.device)
        (stdout, stderr) = execute(cmd, shell = False, raiseError = False)
        return stdout != ""


    def start(self):
        self.createdev()
        self.setchannel()
        self.setessid()
        self.setantenna()
        self.ifup()
        self.settxpower()

        
    def main(self):
        "Main method of the madwifi object"

        self.parse_option()
        self.set_option()
        
        # call the corresponding method
        requireroot()
        eval("self.%s()" %(self.action)) 



if __name__ == "__main__":
    Madwifi().main()
