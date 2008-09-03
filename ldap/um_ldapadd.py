#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import tempfile
import ldap
import os
import sys
import getpass
import string
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_functions import execute, CommandFailed, call, requireroot

class LdapAdd(Application):


    def __init__(self):
        Application.__init__(self)

        # initialization of the option parser
        requireroot()
        usage = "usage: %prog"
        self.parser.set_usage(usage)
        self.parser.set_defaults(server = "accountserver",
                         baseDN = "ou=People,dc=umic-mesh,dc=net")

    def run(self):
        # ----------> connect to ldap server
        passwd = getpass.getpass("LDAP admin password: ")        #get the ldap admin password without displaying it
        try:
            l = ldap.open(self.options.server)
            l.simple_bind_s("cn=admin,dc=umic-mesh,dc=net", passwd)
            info("Connected to server.")
        except ldap.LDAPError, error_message:
            error("Couldn't connect. %s" % error_message)
            exit()
        
        # ----------> finding the maximum uidNumber, so that the new user can get the next
        mid = l.search_s(self.options.baseDN, ldap.SCOPE_SUBTREE, "objectClass=*")
        
        uidNumber = 2000        #minimum for an uidNumber
        for entry in mid:
            try:            #there is one entry at the beginning without uidNumber
                new = (int)(entry[1]["uidNumber"][0])
                if (new > uidNumber):
                    uidNumber = new
            except:
                pass #No uidNumber in entry
        
        # ----------> set user data
        print "Forename: ",
        name=sys.stdin.readline().strip()
        
        print "Lastname: ",
        lastname=sys.stdin.readline().strip()
        
        mail=string.lower(name)+"."+string.lower(lastname)+"@rwth-aachen.de"
        print "Email [def: "+mail+"]: ",
        mail2=sys.stdin.readline().strip()
        if (mail2 != ""):
            mail = mail2
        
        uidNumber = uidNumber+1
        llastname = string.lower(lastname)
        
        # ----------> create ldif files
        tmp = tempfile.NamedTemporaryFile()
        str_tmp1 = """version: 1
dn: uid=%s,ou=People,dc=umic-mesh,dc=net
objectClass: top
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
objectClass: systemQuotas
uid: %s
cn: %s %s
gecos: %s %s
sn: %s
givenName: %s
shadowMax: 99999
shadowWarning: 7
loginShell: /bin/bash
homeDirectory: /home/%s
mail: %s
uidNumber: %u
gidNumber: 100
quota: /dev/hda3:20000000,30000000,0,0
userPassword:
shadowLastChange: 0
""" % (llastname,llastname,name,llastname,name,llastname,llastname,name,llastname,mail,uidNumber)

        tmp.write(str_tmp1)
        tmp.flush()        

        tmp2 = tempfile.NamedTemporaryFile()
        str_tmp2 = """version: 1
dn: cn=%s,ou=auto.home,ou=automount,ou=admin,dc=umic-mesh,dc=net
cn: %s
objectClass: top
objectClass: automount
automountInformation: -fstype=nfs,rw,hard,intr,nodev,exec,nosuid,relatime,rsize=8192,
 wsize=8192  accountserver:/home/%s
""" % (llastname,llastname,llastname)

        tmp2.write(str_tmp2)
        tmp2.flush()

        # ----------> call ldapadd to create user
        exec1 = call("ldapadd -x -D \"cn=admin,dc=umic-mesh,dc=net\" -w \"%s\" -f %s" % (passwd,tmp.name))
        if (exec1 == 0):
            info("Added user.")
            exec2 = call("ldapadd -x -D \"cn=admin,dc=umic-mesh,dc=net\" -w \"%s\" -f %s" % (passwd, tmp2.name))
            if (exec2 == 0):
                info("Automount information added.")
            else:
                error("Adding automount information failed.\nDeleting user.")
                rid = l.delete("cn=%s,ou=auto.home,ou=automount,ou=admin,dc=umic-mesh,dc=net" % llastname)
                l.result(rid)
                exit()
        else:
            error("Adding user failed.")
            exit()
        
        # ----------> add user to groups
        def_groups = ['um-user','um-webuser']
        mod_attrs = [( ldap.MOD_ADD, 'memberUid', llastname )]
        for gr in def_groups:
            l.modify_s('cn='+gr+',ou=Group,dc=umic-mesh,dc=net', mod_attrs)
            info("Added user %s to group %s" % (llastname, gr))
        
        # ----------> create home directory
        call("su %s -c exit" % llastname)

        # ----------> close connection and remove temp files
        l.unbind_s()
        tmp.close()
        tmp2.close()
        
        
    def main(self):
        self.parse_option()
        self.set_option()
        self.run()



if __name__ == "__main__":
    LdapAdd().main()
