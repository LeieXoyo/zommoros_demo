from datetime import datetime, timedelta
import pytz

from backtrader import date2num

def dt_plus8(dt):
    return dt + timedelta(hours=8)

def trim_dt(dt, fmt_style='%Y-%m-%d %H:%M:%S'):
    return dt.strftime(fmt_style)

def trim_dt_plus8(dt):
    return trim_dt(dt_plus8(dt))

def dt_from_str(str, fmt_style='%Y-%m-%d %H:%M:%S'):
    return datetime.strptime(str, fmt_style)

def dt_from_str_to_num(str, fmt_style='%Y-%m-%d %H:%M:%S'):
    return date2num(dt_from_str(str, fmt_style), tz=pytz.timezone('Asia/Shanghai'))
    