from os import path, makedirs
from datetime import datetime, timedelta
CONSTANT_LOGS_PATH = path.join("logs")
CONSTANT_CLIENTBOOK_NAME = path.join("client-book.ini")
CONSTANT_DEFAULT_CLIENTNAME = "Self"
CONSTANT_DEFAULT_CLIENTSLUG = CONSTANT_DEFAULT_CLIENTNAME.lower()


if not path.exists(CONSTANT_LOGS_PATH):
    makedirs(CONSTANT_LOGS_PATH)


def timestamp(time = datetime.now()):
    return time.strftime("%m/%d/%Y %I:%M%p")  

def parse_timestamp(line):
    return datetime.strptime(line.split("-")[1].strip().split(']')[0].strip(), "%m/%d/%Y %I:%M%p")





def clocktime(seconds):
    if isinstance(seconds, timedelta):
        seconds = seconds.total_seconds()
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return "{:02d}:{:02d}:{:02d}".format(int(hours), int(minutes), int(seconds))

def clocktime_parse(time_str):
    x = datetime.strptime(time_str, '%H:%M:%S')
    seconds = x.hour*3600 + x.minute*60 + x.second
    return seconds

def as_clocktime(td: timedelta):
    seconds = td.total_seconds()
    h, m, s = map(int, [seconds // 3600, seconds % 3600 // 60, seconds % 60])
    return f"{h}:{m}:{s}"


