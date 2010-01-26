#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import tempfile
import ldap
import sys
import string
import md5
import base64
from ldif import LDIFParser
from ldap.modlist import addModlist
from random import choice       # to generate a user password
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_functions import execute, CommandFailed, call, requireroot

class LdapAdd(Application):
    def __init__(self):
        Application.__init__(self)

        # initialization of the option parser
        requireroot()
        usage = "usage: %prog\nUsername and all details will be asked at runtime.\nHome directory will be /home/<LASTNAME>"
        self.parser.set_usage(usage)
        self.parser.set_defaults(server = "accountserver",
                         baseDN = "ou=People,dc=umic-mesh,dc=net",
                         passfile = "/etc/ldap.secret"
                    )
        self.parser.add_option("-l", "--ldap-server", metavar = "SERVER",
                               action = "store", dest = "server",
                               help = "The server at which the LDAP directory is located [default: %default]")
        self.parser.add_option("-d", "--baseDN", metavar = "baseDN",
                               action = "store", dest = "baseDN",
                               help = "The base DN define at which node the search should originate [default: %default]")
        self.parser.add_option("-y", "--passfile", metavar = "FILE",
                               action = "store", dest = "passfile",
                               help = "The file for the admin password [default: %default]")

        self.parser.add_option("-g", "--group", metavar = "GROUP",
                               action = "store", dest = "group",
                               help = "Adds user to the given group (only works with -u)")

        self.parser.add_option("-u", "--user", metavar = "UID",
                               action = "store", dest = "uid",
                               help = "User to add to group")

    def run(self):
        class AddLDIF(LDIFParser):
            def __init__(self, input, ldap_handle):
                self.ldap_handle = ldap_handle
                LDIFParser.__init__(self, input)

            def handle(self, dn, entry):
                if not dn:
                    return
                modlist = addModlist(entry)
                self.ldap_handle.add_s(dn, modlist)

        passwd=file(self.options.passfile).readline()
        passwd=passwd.strip()
        # connect to ldap server
        try:
            l = ldap.open(self.options.server)
            l.simple_bind_s("cn=admin,dc=umic-mesh,dc=net", passwd)
            info("Connected to server.")
        except ldap.LDAPError, error_message:
            error("Couldn't connect. %s" % error_message)
            sys.exit(1)

        # add user to ONE group
        if (self.options.group):
            if (self.options.uid):
                # does group exists?
                mid = l.search_s("ou=Group,dc=umic-mesh,dc=net", ldap.SCOPE_SUBTREE, "objectClass=*")
                gr_exists = 0
                for gr in mid:
                    try:
                        if str(gr[1]['cn'][0]) == str(self.options.group): gr_exists = 1
                    except:
                        pass

                # does user exists?
                mid = l.search_s("ou=People,dc=umic-mesh,dc=net", ldap.SCOPE_SUBTREE, "objectClass=*")
                usr_exists = 0
                for usr in mid:
                    try:
                        if usr[1]['uid'][0] == self.options.uid: usr_exists = 1
                    except:
                        pass

                if usr_exists:
                    if gr_exists:
                        mod_attrs = [( ldap.MOD_ADD, 'memberUid', self.options.uid )]
                        l.modify_s('cn=%s,ou=Group,dc=umic-mesh,dc=net' %self.options.group, mod_attrs)
                        info("User %s added to group %s." %(self.options.uid, self.options.group))
                    else: error("Group does not exist.")
                else: error("User does not exist.")
            else:
                error("No user given. Use option -u !")

            # do nothing else than adding user to one group
            sys.exit(0)

        # finding the maximum uidNumber, so that the new user can get the next
        mid = l.search_s(self.options.baseDN, ldap.SCOPE_SUBTREE, "objectClass=*")

        uidNumber = 2000        #minimum for an uidNumber
        for entry in mid:
            try:            #there is one entry at the beginning without uidNumber
                new = (int)(entry[1]["uidNumber"][0])
                if (new > uidNumber):
                    uidNumber = new
            except:
                pass #No uidNumber in entry

        # set user data
        print "Given name: ",
        name=sys.stdin.readline().strip()

        sys.stdout.softspace = 0        #to prevent leading space
        print "Lastname: ",
        lastname=sys.stdin.readline().strip()

        mail="%s.%s@rwth-aachen.de" %(string.lower(name.replace(" ",".")), string.lower(lastname))

        sys.stdout.softspace = 0
        print "Email [def: %s]: " %mail ,
        mail2=sys.stdin.readline().strip()
        if (mail2 != ""):
            mail = mail2

        uidNumber = uidNumber+1
        llastname = string.lower(lastname)

        # create ldif files
        tmp = tempfile.NamedTemporaryFile()

        size = 9
        upasswd = ''.join([choice(string.letters + string.digits) for i in range(size)])
        sys.stdout.softspace = 0
        print "Password will be: %s" % upasswd
        upasswd_md5 = base64.encodestring(md5.new(str(upasswd)).digest())

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
shadowLastChange: 0
shadowMax: 99999
shadowWarning: 7
loginShell: /bin/bash
homeDirectory: /home/%s
mail: %s
uidNumber: %u
gidNumber: 100
quota: /dev/hda3:20000000,30000000,0,0
userPassword: {MD5}%s
shadowLastChange: 0
""" % (llastname,llastname,name,lastname,name,lastname,llastname,name,llastname,mail,uidNumber,upasswd_md5)

        tmp.write(str_tmp1)
        tmp.flush()
        tmp.seek(0)

        parser = AddLDIF(tmp, l)

        try:
            parser.parse()
        except ldap.LDAPError, error_message:
            error("Error: %s" %str(error_message))
            error("Giving up.")
	        sys.exit(1)

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
        tmp2.seek(0)

        parser = AddLDIF(tmp2, l)
        try:
                parser.parse()
        except ldap.LDAPError, error_message:
                error("Error: %s" %str(error_message))
                error("Adding automount information failed.\nDeleting user.")
                rid = l.delete("uid=%s,ou=People,dc=umic-mesh,dc=net" % llastname)
                exit(1)

        # add user to groups
        def_groups = ['um-user','um-webuser']
        mod_attrs = [( ldap.MOD_ADD, 'memberUid', llastname )]
        for gr in def_groups:
            l.modify_s('cn=%s,ou=Group,dc=umic-mesh,dc=net' %gr, mod_attrs)
            info("Added user %s to group %s" % (llastname, gr))

        # create home directory
        call("su %s -c exit" % llastname)

        # close connection and remove temp files
        l.unbind_s()
        tmp.close()
        tmp2.close()

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()


if __name__ == "__main__":
    LdapAdd().main()

