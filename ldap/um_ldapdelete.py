#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import ldap
import re
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
                                 baseDN = "ou=People,dc=umic-mesh,dc=net")

    def run(self):
	# ----------> connect to ldap server
	passwd = getpass.getpass()	#get the ldap admin password without displaying it
	try:
                l = ldap.open(self.options.server)
                l.simple_bind_s("cn=admin,dc=umic-mesh,dc=net", passwd)
                print "Connected to server."
        except ldap.LDAPError, error_message:
                print "Couldn't connect. %s" % error_message
                exit()

	# ----------> get uid
	print "UID: ",
	uid=sys.stdin.readline().strip()

	# ----------> delete user from groups
	mid = l.search_s("ou=Group,dc=umic-mesh,dc=net", ldap.SCOPE_SUBTREE, "objectClass=*")
	groups = []
	for entry in mid:
                try:
                        gr = entry[1]['memberUid']
                        if (uid in gr):
                                groups.append(entry[1]['cn'][0])
                except:
                        print "",

	mod_attrs = [( ldap.MOD_DELETE, 'memberUid', uid )]
	for gr in groups:
		l.modify_s('cn='+gr+',ou=Group,dc=umic-mesh,dc=net', mod_attrs)
		print "Deleted user %s from group %s" % (uid, gr)
	
	# ----------> delete user from automount
	rid = l.delete('cn='+uid+',ou=auto.home,ou=automount,ou=admin,dc=umic-mesh,dc=net')
	l.result(rid)
	print "Deleted user %s from automount" % uid
	
	# ----------> delete user
	rid = l.delete('uid='+uid+',ou=People,dc=umic-mesh,dc=net')
	l.result(rid)
	print "Deleted user %s" % uid

	# ----------> close connection
	l.unbind_s()
	

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()



if __name__ == "__main__":
    LdapDelete().main()
