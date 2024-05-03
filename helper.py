import gzip
import hashlib
import shutil
from datetime import datetime, timezone
import dateparser
import pytz
import requests
import logging
import sys
from genshi.template import NewTextTemplate

####################
#
# Helper functions
#
####################


def log_setup(loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)

    logging.basicConfig(
        level=numeric_level,
        encoding='utf-8',
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("python.log"), logging.StreamHandler(sys.stdout)],
    )


def debug(*arguments, log_type='debug', sep=' '):
    getattr(logging, log_type)(sep.join(str(a) for a in arguments))


def info(*arguments, log_type='info', sep=' '):
    getattr(logging, log_type)(sep.join(str(a) for a in arguments))


def warning(*arguments, log_type='warning', sep=' '):
    getattr(logging, log_type)(sep.join(str(a) for a in arguments))


def error(*arguments, log_type='error', sep=' '):
    getattr(logging, log_type)(sep.join(str(a) for a in arguments))


def critical(*arguments, log_type='critical', sep=' '):
    getattr(logging, log_type)(sep.join(str(a) for a in arguments))


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


# Acquire a Genshi Text Template object for our template pattern
def get_genshi_template(template_text):
    return NewTextTemplate(template_text)


# Apply the Genshi Text Template to the record and return the generated output
def apply_genshi_template(template, record):
    # template is the string from the config.yml
    # record is the record array for one line of the source
    output = str(template.generate(dict=record)).strip()
    debug("Template output:",output)
    return output


def skip_array(skip_text):
    if type(skip_text) is str:
        return eval('['+skip_text+']')
    if type(skip_text) is int:
        return eval('['+str(skip_text)+']')
    return eval('['+skip_text.astype(str)+']')


def get_separator(delimiter):
    if delimiter == 'tab':
        return '\t'
    elif delimiter == 'comma':
        return ','
    else:
        return None


def download(download_url, filepath):
    info("Downloading", download_url, "as", filepath)
    response = requests.get(download_url)
    response.raise_for_status()
    open(filepath, 'wb').write(response.content)
    info("Completed download of", filepath)
    return response


def get_md5(filename_with_path):
    file_hash = hashlib.md5()
    with open(filename_with_path, "rb") as fp:
        while chunk := fp.read(8192):
            file_hash.update(chunk)
        debug(file_hash.digest())
        debug(file_hash.hexdigest())  # to get a printable str instead of bytes
    return file_hash.hexdigest()


def gunzip_file(from_file_path, to_file_path):
    debug("Unzipping", from_file_path, "to", to_file_path)
    with gzip.open(from_file_path, 'rb') as f_in:
        with open(to_file_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    info("Completed gunzip", to_file_path)


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
