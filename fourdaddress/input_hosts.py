import os
import sys
import re

from entry import Entry

HOSTS_RE = re.compile(r'^(?P<ip>\d+[.]\d+[.]\d+[.]\d+)\s*'
                + r'(?P<hostname>[-\w]+)\s*'
                + r'(?P<comment>[#].*)*$')

def get_hosts(hosts_path):

    lines = []
    entries = []

    with open(hosts_path, 'r') as hosts_fh:
        lines = [l.strip() for l in hosts_fh]
        lines = [l for l in lines if l and not l.startswith('#')]

    for line in lines:
        line_match = HOSTS_RE.search(line)
        try:
            line_dict = line_match.groupdict()
            ip = line_dict['ip']
            hostname = line_dict['hostname']

        except KeyError:
            #mandatory item not found
            continue

        except AttributeError:
            #regex didn't match at all
            continue

        #optional
        comment = line_dict.get('comment', '')
        if comment:
            comment = comment.strip('#')

        entry = Entry(ip=ip, hostname=hostname, comment=comment)
        entries.append(entry)

    return entries


