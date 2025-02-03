import logging
import os
import subprocess
import time

logger = logging.getLogger(__name__)

INSTALL_DIR, _ = os.path.split(__file__)
ban_exp = os.path.join(INSTALL_DIR, 'ban.exp')
unban_exp = os.path.join(INSTALL_DIR, 'unban.exp')

def ban_ip(fortigate, client_ip, ban_time):
    fg_user = fortigate['fg_user']
    fg_passwd = fortigate['fg_passwd']
    fg_host = fortigate['fg_host']
    fg_vdom = fortigate['fg_vdom']

    #user host passwd vdom ip time
    args = [
            ban_exp, 
            fg_user, 
            fg_host, 
            fg_passwd, 
            fg_vdom, 
            client_ip, 
            str(ban_time)]
    #python3.6 version of this.
    #p = subprocess.check_output(args, universal_newlines=True, stderr=subprocess.STDOUT)
    #r = p.returncode

    #if r:
    #    if 'disconnect' in p.output:
    #        logger.error(f'ssh connection to {fg_host} failed')

    #return r
    try:
        p = subprocess.check_output(args, universal_newlines=True, stderr=subprocess.STDOUT)
        return 0

    except subprocess.CalledProcessError as e:
        if 'disconnect' in e.output:
            logger.error('failed ssh connection to {}'.format(fg_host))
            return 1
         
def unban_ip(fortigate, client_ip):
    fg_user = fortigate['fg_user']
    fg_passwd = fortigate['fg_passwd']
    fg_host = fortigate['fg_host']
    fg_vdom = fortigate['fg_vdom']

    #user host passwd vdom ip 
    args = [
            unban_exp, 
            fg_user, 
            fg_host, 
            fg_passwd, 
            fg_vdom, 
            client_ip]
    
    try:
        p = subprocess.check_output(args, universal_newlines=True, stderr=subprocess.STDOUT)
        return 0

    except subprocess.CalledProcessError as e:
        if 'disconnect' in e.output:
            logger.error('failed ssh connection to {}'.format(fg_host))
            return 1

