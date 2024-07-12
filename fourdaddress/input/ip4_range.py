import os
import sys
import ipaddress
import math

from entry import Entry

def ip4_range(start_ip4, end_ip4):
    entries = []

    start_ip4 = ipaddress.ip_address(start_ip4)
    end_ip4 = ipaddress.ip_address(end_ip4)

    range_len = int(end_ip4)-int(start_ip4)
    range_len += 1 #account for first ip
    range_host = math.ceil(math.log(range_len,2))
    range_mask = 32 - range_host
    range_cidr = f'{start_ip4}/{range_mask}'
   
    #not strictly correct since start_ip has host bits set,
    # but this will easily give us a range of IP's from start 
    # to end, that can be filtered down as needed
    range_network = ipaddress.ip_network(range_cidr, strict=False)
    for host_ip in range_network.hosts():
        if start_ip4 <= host_ip <= end_ip4:
            entry = Entry(host_ip)
            entries.append(entry)

    return entries
