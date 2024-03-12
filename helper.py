import gzip
import hashlib
import shutil
from datetime import datetime, timezone
import dateparser
import pytz
import requests
import logging

####################
#
# Helper functions
#
####################


def debug(*arguments, logtype='debug', sep=' '):
    getattr(logging, logtype)(sep.join(str(a) for a in arguments))


def info(*arguments, logtype='info', sep=' '):
    getattr(logging, logtype)(sep.join(str(a) for a in arguments))


def warning(*arguments, logtype='warning', sep=' '):
    getattr(logging, logtype)(sep.join(str(a) for a in arguments))


def error(*arguments, logtype='error', sep=' '):
    getattr(logging, logtype)(sep.join(str(a) for a in arguments))


def critical(*arguments, logtype='critical', sep=' '):
    getattr(logging, logtype)(sep.join(str(a) for a in arguments))


def str_to_datetime(date_str, date_format):
    # first try the configured format
    try:
        return datetime.strptime(str(date_str), date_format).replace(tzinfo=pytz.UTC)
    # then try dateparser generic handling
    except (ValueError, TypeError):
        return dateparser.parse(str(date_str)).replace(tzinfo=pytz.UTC)


epoch: datetime = str_to_datetime('01/01/1970', '%m/%d/%Y').replace(tzinfo=pytz.UTC)
today = datetime.now(timezone.utc)


def date_to_days(dt):
    return (dt-epoch).days


def date_to_age(dt):
    return (today-dt).days


def get_days(date_str, date_format):
    if date_str == "-" or date_str == "NA":
        return -1
    dt = str_to_datetime(date_str, date_format)
    return date_to_days(dt)


def get_age(date_str, date_format):
    if date_str == "-" or date_str == "NA":
        return -1
    dt = str_to_datetime(date_str, date_format)
    return date_to_age(dt)


def apply_template(template, record):
    # template is the string from the config.yml
    # record is the record array for one line of the source
    output = template
    for key, value in record.items():
        # substitute value for instances of {key} in template
        param = '{' + str(key) + '}'
        output = output.replace(param, str(value))
    return output


def skip_array(skiptext):
    if type(skiptext) is str:
        return eval('['+skiptext+']')
    if type(skiptext) is int:
        return eval('['+str(skiptext)+']')
    return eval('['+skiptext.astype(str)+']')


def get_separator(delim):
    if delim == 'tab':
        return '\t'
    elif delim == 'comma':
        return ','
    else:
        return None


def download(downloadurl, filepath):
    debug("Downoading", downloadurl, "as", filepath)
    req = requests.get(downloadurl)
    open(filepath, 'wb').write(req.content)
    info("Completed download of", filepath)
    return req


def get_md5(filename_with_path):
    file_hash = hashlib.md5()
    with open(filename_with_path, "rb") as fp:
        while chunk := fp.read(8192):
            file_hash.update(chunk)
        debug(file_hash.digest())
        debug(file_hash.hexdigest())  # to get a printable str instead of bytes
    return file_hash.hexdigest()


def gunzip_file(fromfilepath, tofilepath):
    debug("Ungzipping", fromfilepath, "to", tofilepath)
    with gzip.open(fromfilepath, 'rb') as f_in:
        with open(tofilepath, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    info("Completed gunzip", tofilepath)


def get_join_precedence(join_group):
    if join_group == 'variation-id':
        return 0
    elif join_group == 'gene-symbol':
        return 1
    elif join_group == 'hgnc-id':
        return 2
    elif join_group is not None:
        return 3
    else:
        return 4


# Datetime formats seen in current sources:
#
# Mon Nov 02 21:15:11 UTC 2020
# %a %b %d %H:%M%S %Z %Y
#
# 2016-06-08T14:14:30Z
# %Y-%m-%dT%H:%M:%SZ
#
# 2018-06-07T16:00:00.000Z
# %Y-%m-%dT%H:%M:%S.%fZ
#
# Wed, 01 Feb 2023 00:00:00 -0000
# %a, %d %b %Y %H:%M:%S %z
#
# Mar 23, 2023
# %b %d, %Y
#
# 2020-12-24
# %Y-%m-%d
#
# 2020-06-18 13:31:17
# %Y-%m-%d %H:%M:%S
#
# datetime.strptime('31/01/22 23:59:59.999999',
#                   '%d/%m/%y %H:%M:%S.%f')
#
# Either keep a list of tokens for approved formats, or use the format string as the configuration