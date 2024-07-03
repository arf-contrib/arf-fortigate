class Entry():
    def __init__(self, ip, hostname='', comment=''):
        self.ip = ip
        _hostname = hostname if hostname else str(ip)
        _hostname = _hostname.lower()
        self.hostname = _hostname

        _comment = '' if comment==None else comment
        self.comment = _comment
