#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ldap
import re

from um_functions import *
from um_application import Application

class Applyquotas(Application):
    "Class to apply user system quotas from LDAP"

    def __init__(self):
        Application.__init__(self)

    def main(self):

        self.parse_option()
        self.set_option()

        # Parses a quota line from LDAP.
        # Syntax definition: see quota.schema
        parse_quota_re = re.compile('([^:]+):([0-9]+),([0-9]+),([0-9]+),([0-9]+)$')

        # Query ldap server for users with systemQuotas
        l = ldap.open("accountserver")
        l.simple_bind_s("", "")
        mid = l.search("ou=People,dc=umic-mesh,dc=net", ldap.SCOPE_SUBTREE, "objectClass=systemQuotas")

        (type, result) = l.result(msgid = mid)
        assert(type == ldap.RES_SEARCH_RESULT)

        # For each such user, apply quota settings
        for r in result:
            # r is a tuple, the dictionary with the ldap values is the second value.
            user = r[1]['uid'][0]
            for q in r[1]['quota']:
                try:
                    # file system, soft blocks, hard blocks, soft inodes, hard inodes.
                    (fs,sblocks,hblocks,sinodes,hinodes) = parse_quota_re.match(q).groups()
                    info("Apply quota: user=%s, disk=%s, sblocks=%s, hblocks=%s, sinodes=%s, hinodes=%s"
                        % (user, fs, sblocks, hblocks, sinodes, hinodes))
                    execute(["/usr/sbin/setquota", "-u", user, sblocks, hblocks, sinodes, hinodes, fs],
                            shell=False)
                except AttributeError, inst:
                    error("Syntax error in quota definition: user=%s, quota='%s'." % (user, quota))
                except CommandFailed, inst:
                    error("Setting quota failed. Reason:")
                    error(inst)
                    error("Error message %s" % inst.stderr)

if __name__ == "__main__":
    Applyquotas().main()
