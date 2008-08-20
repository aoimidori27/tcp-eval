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
from um_functions import execute, CommandFailed, call

class LdapAdd(Application):


    def __init__(self):
        Application.__init__(self)

        # initialization of the option parser
        usage = "usage: %prog"
        self.parser.set_usage(usage)
        self.parser.set_defaults(server = "accountserver",
                                 baseDN = "ou=People,dc=umic-mesh,dc=net")

    def run(self):
	# ----------> connect to ldap server
	passwd = getpass.getpass(prompt="LDAP admin password:")	#get the ldap admin password without displaying it
	try:
		l = ldap.open(self.options.server)
        	l.simple_bind_s("cn=admin,dc=umic-mesh,dc=net", passwd)
		info("Connected to server.")
	except ldap.LDAPError, error_message:
		error("Couldn't connect. %s" % error_message)
		exit()
	
	# ----------> finding the maximum uidNumber, so that the new user can get the next
	mid = l.search_s(self.options.baseDN, ldap.SCOPE_SUBTREE, "objectClass=*")
	
	uidNumber = 2000	#minimum for an uidNumber
	for entry in mid:
		try:		#there is one entry at the beginning without uidNumber
			new = (int)(entry[1]["uidNumber"][0])
			if (new > uidNumber):
				uidNumber = new
		except:
			print "", #No uidNumber in entry
	
	# ----------> set user data
	print "Name: ",
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
	tmp = open('/tmp/script.ldap.tmpp.ldif', 'w')
	tmp.write("version: 1\n")
	tmp.write("dn: uid="+llastname+",ou=People,dc=umic-mesh,dc=net\n")
	tmp.write("objectClass: top\n")
	tmp.write("objectClass: inetOrgPerson\n")
	tmp.write("objectClass: posixAccount\n")
	tmp.write("objectClass: shadowAccount\n")
	tmp.write("objectClass: systemQuotas\n")
	tmp.write("uid: "+llastname+"\n")
	tmp.write("cn: "+name+" "+lastname+"\n")
	tmp.write("gecos: "+name+" "+lastname+"\n")
	tmp.write("sn: "+lastname+"\n")
	tmp.write("givenName: "+name+"\n")
	tmp.write("shadowMax: 99999\n")
	tmp.write("shadowWarning: 7\n")
	tmp.write("loginShell: /bin/bash\n")
	tmp.write("homeDirectory: /home/"+llastname+"\n")
	tmp.write("mail: "+mail+"\n")
	tmp.write("uidNumber: "+(str)(uidNumber)+"\n")
	tmp.write("gidNumber: 100\n")
	tmp.write("quota: /dev/hda3:20000000,30000000,0,0\n")
	tmp.write("userPassword:\n")
	tmp.write("shadowLastChange: 0\n")
	tmp.close()
	
	tmp2 = open('/tmp/script.ldap.tmpp2.ldif', 'w')
	tmp2.write("version: 1\n")
	tmp2.write("dn: cn="+llastname+",ou=auto.home,ou=automount,ou=admin,dc=umic-mesh,dc=net\n")
	tmp2.write("cn: "+llastname+"\n")
	tmp2.write("objectClass: top\n")
	tmp2.write("objectClass: automount\n")
	tmp2.write("automountInformation: -fstype=nfs,rw,hard,intr,nodev,exec,nosuid,relatime,rsize=8192,\n")
 	tmp2.write(" wsize=8192  accountserver:/home/"+llastname+"\n")
	tmp2.close()

	# ----------> call ldapadd to create user
	exec1 = call("ldapadd -x -D \"cn=admin,dc=umic-mesh,dc=net\" -w \""+passwd+"\" -f /tmp/script.ldap.tmpp.ldif")
	if (exec1 == 0):
		print "Added user."
		exec2 = call("ldapadd -x -D \"cn=admin,dc=umic-mesh,dc=net\" -w \""+passwd+"\" -f /tmp/script.ldap.tmpp2.ldif")
		if (exec2 == 0):
			print "Automount information added."
		else:
			print "Adding automount information failed.\nDeleting user."
			rid = l.delete('cn='+llastname+',ou=auto.home,ou=automount,ou=admin,dc=umic-mesh,dc=net')
        		l.result(rid)
			exit()
	else:
		print "Adding user failed."
		exit()
	
	# ----------> add user to groups
	def_groups = ['um-user','um-webuser']
	mod_attrs = [( ldap.MOD_ADD, 'memberUid', llastname )]
	for gr in def_groups:
		l.modify_s('cn='+gr+',ou=Group,dc=umic-mesh,dc=net', mod_attrs)
		print "Added user %s to group %s" % (llastname, gr)
	
	# ----------> close connection and remove temp files
	l.unbind_s()
	os.remove('/tmp/script.ldap.tmpp.ldif')
	os.remove('/tmp/script.ldap.tmpp2.ldif')
	
	
    def main(self):
        self.parse_option()
        self.set_option()
        self.run()



if __name__ == "__main__":
    LdapAdd().main()
