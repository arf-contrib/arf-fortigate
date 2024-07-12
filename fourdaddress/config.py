import os
import sys
import logging
import configparser
import ipaddress

logger = logging.getLogger(__name__)

class OptionParsers():
    '''conversion methods for ini section/option to appropriate types'''

    @staticmethod
    def action(section, option, p):
        return p.get(section, option)

    @staticmethod
    def hosts(section, option, p):
        return p.get(section, option, fallback='')

    @staticmethod
    def start_ip(section, option, p):
        s = p.get(section, option)
        v = ipaddress.ip_address(s)
        return v

    @staticmethod
    def end_ip(section, option, p):
        s = p.get(section, option)
        v = ipaddress.ip_address(s)
        return v

    @staticmethod
    def prefix(section, option, p):
        return p.get(section, option)

    @staticmethod
    def tsv(section, option, p):
        return p.get(section, option)

    @staticmethod
    def csv(section, option, p):
        return p.get(section, option)

    @staticmethod
    def ip(section, option, p):
        return p.getint(section, option)

    @staticmethod
    def hostname(section, option, p):
        return p.getint(section, option)

    @staticmethod
    def comment(section, option, p):
        return p.getint(section, option)

    @staticmethod
    def source_host(section, option, p):
        return p.get(section, option)

    @staticmethod
    def source_vdom(section, option, p):
        return p.get(section, option)

    @staticmethod
    def source_token(section, option, p):
        return p.get(section, option)

    @staticmethod
    def source_verify(section, option, p):
        return p.getboolean(section, option)

    @staticmethod
    def dest_host(section, option, p):
        return p.get(section, option)

    @staticmethod
    def dest_vdoms(section, option, p):
        s = p.get(section, option)
        return [i for i in s.split(',')]

    @staticmethod
    def dest_token(section, option, p):
        return p.get(section, option)

    @staticmethod
    def dest_verify(section, option, p):
        return p.getboolean(section, option)

    @staticmethod
    def firewall_address(section, option, p):
        s = p.get(section, option)
        return [i for i in s.split(',')]

    @staticmethod
    def firewall_addrgrp(section, option, p):
        s = p.get(section, option)
        return [i for i in s.split(',')]

    @staticmethod
    def application_group(section, option, p):
        s = p.get(section, option)
        return [i for i in s.split(',')]

    @classmethod
    def get_option_func(cls, option):
        '''returns parser function for option, configparser instance'''
        try:
            return getattr(cls, option)
        except AttributeError:
            return None

def parse_config(path):
    parser = configparser.ConfigParser()
    parser.read(path)

    parsed = {}
    for section in parser:
        if section == 'DEFAULT':
            continue

        parsed[section] = {}
        for option in parser[section]:
            option_parser = OptionParsers.get_option_func(option)
            if not option_parser:
                logger.warning(f'unsupported option {option}')
                continue

            value = option_parser(section, option, parser)
            parsed[section][option] = value 
    return parsed
