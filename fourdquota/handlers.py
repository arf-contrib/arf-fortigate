import os
import sys
import logging
import datetime
import json

from fvhelper import fortiview_client_deltas
from util import get_tick, formatbytes

logger = logging.getLogger(__name__)

def enable(args, client_data, clients):
    #save default quota value
    client_data['_quota'] = args.quota

    #reset all clients to default quota
    for client_ip in clients:
        client_data['quota'][client_ip] = args.quota
 
    return client_data

def disable(args, client_data, clients):
    #set default quota value to 0 (unlimited)
    client_data['_quota'] = 0

    #set all clients to 0 (unlimited)
    for client_ip in clients:
        client_data['quota'][client_ip] = 0

    return client_data

def reset(args, client_data):
    _quota = client_data['_quota']
    client_ip = args.client
    client_data['quota'][client_ip] += _quota
    client_data['banned'][client_ip] = False

    return client_data

def exempt(args, client_data):
    client_ip = args.client
    client_data['quota'][client_ip] = 0
    client_data['banned'][client_ip] = False

    return client_data
 
def new_day(args, client_data, clients):

    #reset _day_tick so our day starts now
    client_data['_day_tick'] = get_tick()

    #reset usage to 0
    for client_ip in clients:
        client_data['usage'][client_ip] = 0

    _quota = client_data['_quota']

    #reset banned status
    for client_ip in clients:
        client_data['banned'][client_ip] = False

    #if quotas sizes were temporarily increased yesterday,
    # reset them to default. 
    #if this specific device was exempted from the quota,
    # continue that exemption.

    for client_ip in clients:
        if client_data['quota'][client_ip] > _quota:
            client_data['quota'][client_ip] = _quota

    return client_data

def update(args, client_data, clients, fortigate, then, now):
    
    #define at top to accomodate early returns
    banned_clients = []

    if then == 0:
        #early return!
        logger.info('waiting for full update interval')
        return client_data, banned_clients

    client_deltas = fortiview_client_deltas(
            fortigate, 
            clients, 
            then, 
            now)

        
    for client_ip in clients:
        #update usage in struct
        client_data['usage'][client_ip] += client_deltas.get(client_ip, 0)

        #compare after update
        client_usage = client_data['usage'][client_ip]
        client_quota = client_data['quota'][client_ip]

        if client_quota == 0:
            # 0 indicates a device is exempt
            continue

        elif client_usage >= client_quota:
            banned_clients.append(client_ip)

    return client_data, banned_clients

def status(args, client_data, clients):
    status_lines = []

    now = get_tick()
    then = client_data['_day_tick']
    interval = now - then
    h, r = divmod(interval, 3600)
    m, s = divmod(r, 60)

    interval_str = f'{h:02d}:{m:02d}:{s:02d}'
    line = f'Time since --new-day: {interval_str}'
    status_lines.append(line)

    for client_ip in clients:
        client_usage = client_data['usage'][client_ip]
        u = formatbytes(client_usage)
        client_quota = client_data['quota'][client_ip]
        q = formatbytes(client_quota)
        
        if client_quota == 0:
            line = f'{client_ip}: EXEMPT usage {u}'
            status_lines.append(line)
        elif client_usage < client_quota:
            line = f'{client_ip}: UNDER usage {u} quota {q}'
            status_lines.append(line)
        elif client_usage > client_quota:
            line = f'{client_ip}: OVER usage {u} quota {q}'
            status_lines.append(line)

    return status_lines 
