#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import ldap
import os
import sys
import getpass
import string
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_functions import execute, CommandFailed

class LdapDelete(Application):


    def __init__(self):
        Application.__init__(self)

        # initialization of the option parser
        usage = "usage: %prog"
        self.parser.set_usage(usage)
        self.parser.set_defaults(server = "accountserver",
                                 baseDN = "ou=People,dc=umic-mesh,dc=net",
                                 userid = "")
        self.parser.add_option("-u", "--userid",
                               action = "store", dest = "userid",
                               help = "Set the user to remove")

    def run(self):
        # ----------> connect to ldap server
        passwd = getpass.getpass("LDAP admin password: ")        #get the ldap admin password without displaying it
        try:
            l = ldap.open(self.options.server)
            l.simple_bind_s("cn=admin,dc=umic-mesh,dc=net", passwd)
            info("Connected to server.")
        except ldap.LDAPError, error_message:
            error("Couldn't connect: %s" % error_message)
            exit()

        # ----------> get uid
        while (1 == 1):     # if the user doesn't exist do not exit with an error but give it another try
            if not (self.options.userid == ""):
                uid = self.options.userid
            else:
                print "username: ",
                uid = sys.stdin.readline().strip()

            # ----------> delete user from groups
            mid = l.search_s("ou=Group,dc=umic-mesh,dc=net", ldap.SCOPE_SUBTREE, "objectClass=*")
            groups = []
            for entry in mid:
                try:
                    gr = entry[1]['memberUid']
                    if (uid in gr):
                        groups.append(entry[1]['cn'][0])
                except:
                    pass

            mod_attrs = [( ldap.MOD_DELETE, 'memberUid', uid )]
            for gr in groups:
                l.modify_s('cn=%s,ou=Group,dc=umic-mesh,dc=net' % gr, mod_attrs)
                info("Deleted user %s from group %s" % (uid, gr))
        
            # ----------> delete user from automount
            try:
                rid = l.delete('cn=%s,ou=auto.home,ou=automount,ou=admin,dc=umic-mesh,dc=net' % uid)
                l.result(rid)
                info("Deleted user %s from automount" % uid)
                break   # get out of the loop if the user exists
            except ldap.NO_SUCH_OBJECT, error_message:
                error("No such user. %s" % error_message)
                self.options.userid = ""
        
        # ----------> delete user
        rid = l.delete('uid=%s,ou=People,dc=umic-mesh,dc=net' % uid)
        l.result(rid)
        info("Deleted user %s" % uid)

        # ----------> close connection
        l.unbind_s()
        

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()



if __name__ == "__main__":
    LdapDelete().main()
