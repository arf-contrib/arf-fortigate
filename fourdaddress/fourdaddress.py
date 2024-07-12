'''
    fourdquota.py
'''

import os
import sys
import argparse
import logging
import pprint

from config import parse_config
from entry import Entry
from handler import update_vdom_entries, update_vdom_api
from input.hosts import get_hosts
#from ip4_range import ip4_range
#from input_hosts import get_hosts
#from output_text import output_text

#from update_vdom.update import update_vdom_entries

#global variables
READ='read'
WRITE='write'
UPDATE_VDOM='update-vdom'
UPDATE_ADOM='update-adom'

#logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def parse_args():
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter)
   
    parser.add_argument('config')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    config = parse_config(args.config)
    if args.verbose:
        pprint.pprint(config)

    for name, options in config.items():
        action = options.get('action')
        if action == 'update-vdom':
            entries = update_vdom_entries(options)
            update_vdom_api(options, entries)

        elif action == 'sync-vdom':
            pass

