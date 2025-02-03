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

#shut UP about SSL certs, I know!!!
urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)

def fortiview_url(host, vdom, then, now, access_token):
    params = {}
    params['host'] = host
    params['vdom'] = vdom
    params['count'] = 300
    params['device'] = 'disk'
    params['realtime'] = False
    params['report_by'] = 'source'
    params['sort_by'] = 'bytes'
    params['start'] = then 
    params['end'] = now 
    params['access_token'] = access_token

    url_t = Template(
            'https://${host}/api/v2/monitor/fortiview/statistics?'
            + 'vdom=${vdom}'
            + '&count=${count}'
            + '&device=${device}'
            + '&realtime=${realtime}'
            + '&report_by=${report_by}'
            + '&start=${start}'
            + '&end=${end}'
            + '&access_token=${access_token}')
    url = url_t.substitute(**params)
    
    return url

def fortiview_request(url):
    
    #read fortiview
    try:
        r = requests.get(url, verify=False)
        r.raise_for_status()
        fv_resp = r.json()

    except Exception as e:
        logger.error(e)
        sys.exit(1)
   
    results = fv_resp.get('results')
    details = results.get('details')
    deltas = {}

    for detail in details:

        client_ip = detail.get('srcip')
        client_deltabytes = detail.get('bytes')
        deltas[client_ip] = client_deltabytes

    return deltas

def fortiview_client_deltas(fortigate, clients, then, now):

    host = fortigate.get('fg_host') 
    vdom = fortigate.get('fg_vdom')
    token = fortigate.get('fg_token')

    url = fortiview_url(host, vdom, then, now, token)
    deltas = fortiview_request(url)

    return deltas

