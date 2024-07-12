import os
import sys
import logging
import warnings
import json
from string import Template
from urllib.parse import urlencode

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import requests

logger = logging.getLogger(__name__)

#api url templates
fw_addr_base_t = Template('https://${host}/api/v2/cmdb/firewall/address')
fw_addr_name_t = Template('https://${host}/api/v2/cmdb/firewall/address/${name}')
fw_grp_base_t = Template('https://${host}/api/v2/cmdb/firewall/addrgrp')
fw_grp_name_t = Template('https://${host}/api/v2/cmdb/firewall/addrgrp/${name}')
app_grp_base_t = Template('https://${host}/api/v2/cmdb/application/group')
app_grp_name_t = Template('https://${host}/api/v2/cmdb/application/group/${name}')

#api body templates
def fw_addr_body(name='', subnet='', comment='', color=0):
    if not name:
        raise ValueError('firewall address name must not be empty')
    if not subnet:
        raise ValueError('firewall address subnet must not be empty')

    body = {}
    body['name'] = name
    body['type'] = 'ipmask'
    body['subnet'] = subnet
    body['comment'] = comment
    body['color'] = color

    return body

def fw_grp_body(name='', members=[], comment='', color=0):
    if not name:
        raise ValueError('firewall addrgrp name must not be empty')

    body = {}
    body['name'] = name
    body['type'] = 'default'
    body['members'] = members
    body['comment'] = comment
    body['color'] = color

    return body

def app_grp_body(name='', application=[], comment=''):
    if not name:
        raise ValueError('application group name must not be empty')
    if not application:
        raise ValueError('application group list must not be empty')

    body = {}
    body['name'] = name
    body['type'] = 'application'
    body['application'] = application

    return body

#api basic methods

class ApiError(Exception):
    pass


#api endpoint methods
class ApiEndpoint():
    def __init__(self, host='', vdom='', token='', verify=True):
        self.host = host
        self.vdom = vdom
        self.token = token
        self.verify = verify

        if not self.verify:
            requests.packages.urllib3.disable_warnings()

    def _url(self, url_t, name=''): 
        url = url_t.substitute(name=name, host=self.host)
        query = {'vdom':self.vdom,'access_token':self.token}
        url += '?' + urlencode(query)
        return url

    def _request(self, url, method='get', body={}):
        #strip off query string, which includes access_token for logging
        url_safe = url.split('?')[0]

        if method == 'get':
            request_f = requests.get
            request_kwargs = {'verify':self.verify}
        elif method == 'post':
            request_f = requests.post
            request_kwargs = {'json':body,'verify':self.verify}
        elif method == 'put':
            request_f = requests.put
            request_kwargs = {'json':body,'verify':self.verify}

        try:
            r = request_f(url, **request_kwargs)
            r.raise_for_status()
            resp = r.json()
        
        except requests.HTTPError:
            raise ApiError(f'HTTPError for {url_safe}')

        except json.decoder.JSONDecodeError:
            raise ApiError(f'JSONDecodeError for {url_safe}')

        except Exception as e:
            raise ApiError(f'Fatal error for {url_safe}: {e}')

        return resp.get('results', [])


    def create(self, endpoint='', name='', body={}):
        if endpoint == '/firewall/address':
            url_t = fw_addr_base_t
        elif endpoint == '/firewall/addrgrp':
            url_t = fw_grp_base_t
        elif endpoint == '/application/group':
            url_t = app_grp_base_t
        else:
            raise ValueError('Endpoint {endpoint} not supported')

        url = self._url(url_t, name)
        #create = POST request
        return self._request(url, method='post', body=body)


    def read(self, endpoint='', name=''):
        if endpoint == '/firewall/address' and name:
            url_t = fw_addr_name_t
        elif endpoint == '/firewall/address':
            url_t = fw_addr_base_t
        elif endpoint == '/firewall/addrgrp' and name:
            url_t = fw_grp_name_t
        elif endpoint == '/firewall/addrgrp':
            url_t = fw_grp_base_t
        elif endpoint == '/application/group' and name:
            url_t = app_grp_name_t
        elif endpoint == '/application/group':
            url_t = app_grp_base_t

        url = self._url(url_t, name)
        #read = GET request
        return self._request(url, method='get')

    def update(self, endpoint='', name='', body={}):
        if endpoint == '/firewall/address':
            url_t = fw_addr_name_t
        elif endpoint == '/firewall/addrgrp':
            url_t = fw_grp_name_t
        elif endpoint == '/application/group':
            url_t = app_grp_name_t

        url = self._url(url_t, name)
        #update = PUT request
        return self._request(url, method='put', body=body)
