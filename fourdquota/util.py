import datetime

def get_tick():
    dt = datetime.datetime.now(tz=datetime.timezone.utc)
    tick = int(dt.timestamp())
    return tick

def formatbytes(b):
    #display in MB
    mb = b / 1E6
    b_str = f'{mb:.2f} MB'

    return b_str
    

