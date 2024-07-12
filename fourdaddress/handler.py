import os
import sys
import logging
import ipaddress

from vdom_api import (ApiEndpoint,
        ApiError,
        fw_addr_body,
        fw_grp_body,
        app_grp_body)

from input.hosts import get_hosts
from input.ip4_range import ip4_range

logger = logging.getLogger(__name__)

def update_vdom_entries(options, verbose=False):
    entries = []
    prefix = options.get('prefix', '')

    #input from hosts file
    hosts = options.get('hosts', None) 
    if hosts:
        entries.extend(get_hosts(hosts))

    #input from ipv4 start/end ip range
    start_ip = options.get('start_ip', None) 
    end_ip = options.get('end_ip', None)
    if start_ip and end_ip:
        entries.extend(ip4_range(start_ip, end_ip))

    #sort entries
    entries.sort(key=(lambda e:e.ip))
    #append prefix to hostname if defined
    if prefix:
        for entry in entries:
            entry.hostname = prefix + entry.hostname

    #return
    return entries

def update_vdom_api(options, entries, verbose=False):
    host = options.get('dest_host')
    vdoms = options.get('dest_vdoms', ['root'])
    token = options.get('dest_token')
    verify = options.get('dest_verify', True)
    endpoint = '/firewall/address'

    for vdom in vdoms:
        api = ApiEndpoint(host=host, vdom=vdom, token=token, verify=verify)
        try:
            existing_results = api.read(endpoint=endpoint)
        except ApiError as e:
            logger.error(str(e))
            logger.warning(f'{vdom}: list existing addresses failed')
            #skip to next vdom in the list
            continue

        for entry in entries:
            name = entry.hostname
            subnet = f'{entry.ip} 255.255.255.255'
            comment = entry.comment
            body = fw_addr_body(name=name, subnet=subnet, comment=comment)

            match = [r for r in existing_results if r['name'] == name]
            if match and match[0]['subnet'] == subnet:
                continue

            elif match:
                if verbose:
                    logger.info(f'{name}: updating subnet to {subnet}')

                try:
                    api.update(name=name, endpoint=endpoint, body=body)
                except ApiError as e:
                    logger.error(str(e))
                    logger.warning(f'{name}: update subnet failed')

            else:
                if verbose:
                    logger.info(f'{name}: create')

                try:
                    api.create(name=name, endpoint=endpoint, body=body)
                except ApiError as e:
                    logger.error(str(e))
                    logger.warning(f'{name}: create failed')
