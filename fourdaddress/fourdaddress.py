'''
    fourdquota.py
'''

import os
import sys
import argparse

from entry import Entry
from ip4_range import ip4_range
from input_hosts import get_hosts
from output_text import output_text

def parse_args():
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--input-path', action='store', type=str)
    parser.add_argument('--input-format', action='store', type=str)
    parser.add_argument('--nip', action='store', type=int)
    parser.add_argument('--nhost', action='store', type=int)
    parser.add_argument('--ncomment', action='store', type=int)
    parser.add_argument('--start-ip', action='store', type=str)
    parser.add_argument('--end-ip', action='store', type=str)
    parser.add_argument('--stdout', action='store_true')
    parser.add_argument('--output-path', action='store', type=str)
    parser.add_argument('--output-api', action='store', type=str)
    parser.add_argument('--vdom', action='store', type=str)
    parser.add_argument('--prefix', action='store', type=str)
    parser.add_argument('--api-token', action='store', type=str)
    parser.add_argument('--strip', action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    ipath = args.input_path
    ifmt = args.input_format
    #entries = list of tuples
    #entry[0] = ipaddress instance
    #entry[1] = hostname (may be blank)
    #entry[2] = comment (may be blank)

    entries = []
    if args.start_ip and args.end_ip:
        entries = ip4_range(args.start_ip, args.end_ip)
        
    elif ipath and ifmt == 'hosts':
        entries = get_hosts(ipath)

    elif ipath and ifmt == 'csv':
        pass

    elif ipath and ifmt == 'tsv':
        pass

    #output options
    entries.sort(key=(lambda e:e.ip))
    entries_str = output_text(entries, 
            vdom=args.vdom, 
            prefix=args.prefix,
            strip=args.strip)

    if args.stdout:
        print(entries_str)

    if args.output_path:
        path = args.output_path
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        path = os.path.realpath(path)

        try:
            with open(path, 'w') as output_fh:
                output_fh.write(entries_str)
        except OSError:
            sys.exit(1)


