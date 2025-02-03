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

import warnings
#silence annoying warnings that come up on macosx
#macosx only used in dev, production is linux
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import urllib3
    import requests
from urllib.parse import urlencode

#shut UP about SSL certs, I know!!!
urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings()

def address_group_get_url(name, host='', vdom='', access_token=''):
    query = {}
    query['vdom'] = vdom
    query['access_token'] = access_token
    query['datasource'] = 'true'
    query['with_meta'] = 'false'

    url_t = Template('https://${host}/api/v2/cmdb/firewall/addrgrp/${name}')
    url = url_t.substitute(host=host, name=name)
    url += '?' + urlencode(query)

    return url

def address_group_put_url_body(name, member, host='', vdom='', access_token=''):
    url = address_group_get_url(name, host=host, vdom=vdom, access_token=access_token)
    body = {}
    body['name'] = name
    body['member'] = [{'name':m} for m in member]

    return url, body

def update_address_group(name, update_member, remove=False, host='', vdom='', access_token=''):
    #get old members first
    old_url = address_group_get_url(name,
            host=host, 
            vdom=vdom, 
            access_token=access_token)
    old_r = requests.get(old_url, verify=False)
    old_result = old_r.json()

    old_member = []
    for m in old_result['results'][0]['member']:
        old_member.append(m['name'])

    if update_member and not remove:
        update_member.extend(old_member)

    elif update_member and remove:
        temp_member = [m for m in old_member if m not in update_member]
        update_member = temp_member.copy()

    update_url, update_body = address_group_put_url_body(name,
            update_member,
            host=host,
            vdom=vdom,
            access_token=access_token)

    update_r = requests.put(update_url, json=update_body, verify=False)
    return update_r.status_code

def throttle_ip(fortigate, client_ip, ban_time):
    fg_user = fortigate['fg_user']
    fg_passwd = fortigate['fg_passwd']
    fg_host = fortigate['fg_host']
    fg_vdom = fortigate['fg_vdom']
    fg_prefix = fortigate['fg_prefix']
    fg_token = fortigate['fg_token']

    address = fg_prefix + client_ip
    status_code = update_address_group('throttle_devices_group', 
            [address], 
            remove=False, 
            host=fg_host, 
            vdom=fg_vdom, 
            access_token=fg_token)

    code = 0 if status_code==200 else 1
    return code

def unthrottle_ip(fortigate, client_ip):
    fg_user = fortigate['fg_user']
    fg_passwd = fortigate['fg_passwd']
    fg_host = fortigate['fg_host']
    fg_vdom = fortigate['fg_vdom']
    fg_prefix = fortigate['fg_prefix']
    fg_token = fortigate['fg_token']

    address = fg_prefix + client_ip
    status_code = update_address_group('throttle_devices_group', 
            [address], 
            remove=True, 
            host=fg_host, 
            vdom=fg_vdom, access_token=fg_token)
    code = 0 if status_code==200 else 1
    return code

