#!/usr/bin/python3 
import os
import sys
import logging
import datetime
import json
import argparse
import pprint
import argparse
import configparser

from string import Template

from util import get_tick, formatbytes
from handlers import (
        enable,
        disable,
        reset,
        exempt,
        new_day,
        update,
        status)
from fghelper import ban_ip, unban_ip
from addrgrp import throttle_ip, unthrottle_ip

logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#defaults
INSTALL_DIR, _ = os.path.split(__file__)
DEFAULT_CONFIG_PATH = os.path.join(INSTALL_DIR, 'quota.ini')
DEFAULT_TODAY_PATH = os.path.join(INSTALL_DIR, 'today.json')

def read_args():
    #setup parser
    epilog = '''
IMPLEMENTATION
    fortiquota.py provides a per-IP daily quota function for
    Fortigate firewalls, and was written to be used on research 
    vessels. The quota is applied to individual IP addresses, since
    the assumption is that a given network/VLAN onboard may have
    some devices which are always exempted from the quota.

    If an IP address is entered in quota.ini, it will be subject
    to usage tracking and automatic bans from when the 
    --enable --quota <size> option is executed, until the --disable
    option is executed. Specific clients can either be reset, or
    exempted from the quota until the end of the cruise. Clients
    which should always be exempt from the quota should not be
    listed in quota.ini.

    Fortiquota works by reading per-IP bandwidth usage increments from 
    the Fortigate's FortiView API. While the quota is active, this
    script's --update option should be called on a regular interval
    so that usage is updated. Five minutes is the recommended
    update interval. The FortiView query is based upon local traffic 
    logs stored on disk, and requires some setup on the Fortigate:

        * WAN-side firewall rules must log all traffic
        * The Fortigate must have a local disk used for logs
        * The Fortigate must have a JSON API user available. Read only
          is fine.

    While the usage data is pulled from the Forti via HTTP API, the
    bans/unbans are done via ssh, using these commands:

        diagnose user banned-ip add src4 w.x.y.z ban_sec admin
        diagnose user banned-ip delete src4 w.x.y.z

    where w.x.y.z is the client's IP address, and ban_sec is the number
    of seconds remaning in the day. Generating these commands is 
    handled internally within the script, however, the script will
    need the login information for an admin account that has
    permissions to execute diagnose commands on the Fortigate's
    WAN VDOM.


ENABLING/DISABLING QUOTA 

    --enable --quota <quota_size>K/M/G runs at the beginning of the 
        cruise. This enables quota processing for all IP's listed in
        the config file. The --quota option defines the default
        quota size for all devices.

    --disable runs at the end of the cruise. This option sets all
        ip's as exempt from the quota (quota = 0). The rationale
        is to not ban ip's in the event that a crontab entry 
        calling this script with the --update option is present
        between cruises.

DAY-TO-DAY MANAGEMENT
 
    --status prints quota status (exempt, under, over), usage so far,
        and the current daily quota for this device. 
       
    --reset --client w.x.y.z unbans this ip address, and gives them
        another "bucket" of usage. Assuming the default quota size is 
        1000M, and the client reaches this limit and is banned.
        The --reset option would unban the device, and change their
        quota for this specific day to 2000M. Each time the client
        is reset, their quota (for this day) is incremented by the 
        default quota size.

        This is cancelled out by the --new-day option

    --exempt --client w.x.y.z unbans this ip address, and sets their
        quota size to 0 (unlimited).

        All exemptions are cancelled out by the --disable option.

SCRIPTED OPTIONS

    --update is run by crontab, every 5 minutes by default. 

    --new-day is run by crontab at local midnight.

QUOTA.INI SYNTAX
    
    [FORTIGATE]
    FG_HOST=<ip or hostname of Fortigate mgmt interface>
    FG_VDOM=<wan vdom name>
    FG_TOKEN=<api token of REST API admin account. read-only ok.
    FG_USER=<ssh login username>
    FG_PASSWD=<ssh login password>

    [CLIENTS]
    a.b.c.d=True
    ....
    w.x.y.z=True
    # quota is only applied to client ip's listed here, and only if
    # client_ip=True
    '''

    parser = argparse.ArgumentParser(
            description='Daily per-ip quota on Fortigates',
            epilog=epilog,
            formatter_class = argparse.RawDescriptionHelpFormatter) 
    parser.add_argument(
            '--config-path', 
            action='store', 
            default = DEFAULT_CONFIG_PATH) 
    parser.add_argument(
            '--today-path',
            action='store',
            default = DEFAULT_TODAY_PATH)
    parser.add_argument(
            '--update', 
            action='store_true',
            help='update usage and autoban as needed.')
    parser.add_argument(
            '--enable', 
            action='store_true',
            help='enable quota at cruise start. requires --quota')
    parser.add_argument(
            '--disable', 
            action='store_true',
            help='disable quota at cruise end')
    parser.add_argument(
            '--reset', 
            action='store_true',
            help='unban/fresh pool just for today. requires --client')
    parser.add_argument(
            '--exempt', 
            action='store_true',
            help='unban/exempt until end of cruise. requires --client')
    parser.add_argument(
            '--new-day', 
            action='store_true',
            help='called at local midnight. reset all usage/bans')
    parser.add_argument(
            '--client', 
            action='store',
            help='ip address of client.')
    parser.add_argument(
            '--quota', 
            action='store', 
            help='quota size in bytes. supports K/M/G suffix.')
    parser.add_argument(
            '--status',
            action='store_true',
            help='print status of all client IPs in quota')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--debug', action='store_true')

    args = parser.parse_args()

    #validate 
    if args.enable:
        if not args.quota:
            logger.error('--enable requires --quota')
            sys.exit(1)

        #handle suffixes for --quota
        quota = args.quota

        if quota.isdigit():
            conv = 1
        elif quota.endswith('K'):
            quota = quota.strip('K')
            conv = 1E3
        elif quota.endswith('M'):
            quota = quota.strip('M')
            conv = 1E6
        elif quota.endswith('G'):
            quota = quota.strip('G')
            conv = 1E9
        else:
            logger.error('invalid entry for --quota')
            sys.exit(1)

        args.quota = int(quota) * int(conv)


    if args.reset and not args.client:
        logger.error('--reset requires --client')
        sys.exit(1)

    if args.exempt and not args.client:
        logger.error('--exempt requires --client')
        sys.exit(1)

    return args

def read_config(path):
    config_file = configparser.ConfigParser()
    config_file.read(path)

    #key names converted to lowercase
    #FG_HOST in ini becomes fg_host in dict
    fortigate = {k:v for k, v in config_file['FORTIGATE'].items()}

    #convert to simple list of IPs
    clients_keys = [k for k in config_file['CLIENTS'].keys()]
    clients = []

    for key in clients_keys:
        if config_file['CLIENTS'].getboolean(key):
            clients.append(key)

    #pprint.pprint(fortigate)
    #pprint.pprint(clients)

    return fortigate, clients


def empty_client_data(clients):
    client_data = {}

    client_data['_tick'] = 0
    client_data['_day_tick'] = 0
    client_data['_quota'] = 0

    client_data['usage'] = {}
    client_data['quota'] = {}
    client_data['banned'] = {}

    for client_ip in clients:
        client_data['usage'][client_ip] = 0
        client_data['quota'][client_ip] = 0
        client_data['banned'][client_ip] = False

    return client_data

def get_ban_unban(fortigate):
    action = fortigate['fg_action']
    if action == 'throttle':
        return throttle_ip, unthrottle_ip

    else:
        return None, None

def read_client_data(today_path):
    with open(today_path, 'r') as today_fh:
        client_data = json.load(today_fh)  

    return client_data

def save_client_data(today_path, client_data):

    with open(today_path, 'w') as today_fh:
        lines = json.dumps(client_data, indent=2)
        today_fh.write(lines)

if __name__ == '__main__':

    args = read_args()
    config_path = args.config_path
    today_path = args.today_path

    fortigate, clients = read_config(config_path)
    
    #always start with a client_data structure
    try:
        client_data = read_client_data(today_path)

    except OSError:
        client_data = empty_client_data(clients)

    #logger.debug(pprint.pprint(client_data))

    then = client_data['_tick']
    now = get_tick()
    
    if args.enable:
        #new_day first to zero usage THEN enable
        client_data = new_day(args, client_data, clients)
        client_data = enable(args, client_data, clients)  

    elif args.disable:
        client_data = disable(args, client_data, clients)        

    elif args.reset:
        _, unban_f = get_ban_unban(fortigate)
        client_ip = args.client

        if unban_f(fortigate, client_ip) > 0:
            logger.error(f'failed to unban {args.client}')

        client_data = reset(args, client_data)

    elif args.exempt:
        _, unban_f = get_ban_unban(fortigate)
        client_ip = args.client

        if unban_ip(fortigate, args.client) > 0:
            logger.error(f'failed to unban {args.client}')

        client_data = exempt(args, client_data)

    elif args.new_day:
        _, unban_f = get_ban_unban(fortigate)
        for client_ip in clients:
            #boolean value...
            if client_data['banned'][client_ip]:
                if unban_f(fortigate, client_ip) > 0:
                    logger.error(f'failed to unban {args.client}')
       
        client_data = new_day(args, client_data, clients)
    
    elif args.update:
        client_data, banned_clients = update(
                args, 
                client_data, 
                clients, 
                fortigate, 
                then, 
                now) 

        #get ips that exceed quota
        #ban them, then set banned = True 
        ban_f, _ = get_ban_unban(fortigate)
        for client_ip in banned_clients:
            day_tick = client_data['_day_tick']
            ban_time = int((day_tick + 86400) - now)

            if client_data['banned'][client_ip]:
                #don't try and ban them again
                continue

            if ban_f(fortigate, client_ip, ban_time) > 0:
                #ban attempt failed, likely ssh issue...
                logger.error(f'failed to ban {client_ip}')

            else:
                client_data['banned'][client_ip] = True

        #save _tick at the very end of update
        client_data['_tick'] = now 

    elif args.status:
        lines = status(args, client_data, clients)
        for line in lines:
            print(line)

    save_client_data(today_path, client_data)
    sys.exit(0)
