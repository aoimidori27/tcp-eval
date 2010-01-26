#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import ldap
import sys
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_functions import execute, CommandFailed, requireroot

class LdapDelete(Application):
    def __init__(self):
        Application.__init__(self)

        # initialization of the option parser
        requireroot()

        usage = "usage: %prog"
        self.parser.set_usage(usage)
        self.parser.set_defaults(server = "accountserver",
                                 baseDN = "ou=People,dc=umic-mesh,dc=net",
                                 userid = "",
                                 passfile = "/etc/ldap.secret")
        self.parser.add_option("-u", "--userid",
                               action = "store", dest = "userid",
                               help = "Set the user to remove")

        self.parser.add_option("-g", "--group",
                               action = "store", dest = "group",
                               help = "Removes user only from given group")

        self.parser.add_option("-y", "--passfile", metavar = "FILE",
                               action = "store", dest = "passfile",
                               help = "The file for the admin password [default: %default]")

    def run(self):
        # ----------> connect to ldap server
        passwd=file(self.options.passfile).readline()
        passwd=passwd.strip()
        try:
            l = ldap.open(self.options.server)
            l.simple_bind_s("cn=admin,dc=umic-mesh,dc=net", passwd)
            info("Connected to server.")
        except ldap.LDAPError, error_message:
            error("Couldn't connect: %s" % error_message)
            sys.exit(1)

        # ----------> get uid
        while (1 == 1):     # if the user doesn't exist do not exit with an error but give it another try
            if not (self.options.userid == ""):
                uid = self.options.userid
            else:
                print "username: ",
                uid = sys.stdin.readline().strip()

            # ----------> delete user from only ONE group (option -g)
            if (self.options.group):
                mod_attrs = [( ldap.MOD_DELETE, 'memberUid', uid )]
                l.modify_s('cn=%s,ou=Group,dc=umic-mesh,dc=net' %self.options.group, mod_attrs)
                info("User %s removed from group %s" %(uid, self.options.group))
                sys.exit(0)

            # ----------> delete user from all groups
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

