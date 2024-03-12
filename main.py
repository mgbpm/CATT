import argparse
import gzip
import hashlib
import os
import shutil
from datetime import datetime, timezone
import dateparser
from os import access, R_OK
from os.path import isfile

import pandas as pd
import pytz
import requests
import yaml
from sklearn.preprocessing import LabelEncoder
import logging

# TODO:
# ** divide major areas into functions and perhaps files for code clarity and maintainability
# ** do I need to use globals? try to eliminate
# ** fix error when downloading files that have no url configured (suggest manual download?)
# ** os.path.join() for cross platform compatibility
# ** check logic around needs_download during --force
# ** dig more into why "is True" not working as expected in one spot


# TODO:
#  ** look for missing or deprecated columns in data files as compared to dictionaries and mapping files
#    (e.g. recent addition of oncology data)
#    - does dictionary have all the columns, are dictionary columns all present in the file?
#    - are all mapping columns still present in the file?

# TODO:
#  ** when creating dictionary template: analyze column data and set category,
#       onehot, continuous, days, age, based on data types and frequency


#########################
#
# PROGRAM ARGUMENTS
#
#########################

parser = argparse.ArgumentParser(
    prog='clingen-dosage-ai-tools',
    description='Prepares ClinVar, ClinGen, and GenCC sources for use by ML and LLM analysis.',
    add_help=True,
    allow_abbrev=True,
    exit_on_error=True)
# logging level
parser.add_argument('--loglevel', action='store', type=str, default="WARN",
                    help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")

# encoding options
parser.add_argument('--template', action='store_true',
                    help="Generate template output column '<source-name>-template' if specified in config.yml.")
parser.add_argument('--onehot', action='store_true',
                    help="Generate one-hot encodings for columns that support it.")
parser.add_argument('--categories', action='store_true',
                    help="Generate category encodings for columns that support it.")
parser.add_argument('--expand', action='store_true',
                    help="Generate additional rows when specified columns have lists of values (i.e. list of genes).")
parser.add_argument('--map', action='store_true',
                    help="Generate new columns based on mapping group configuration.")
parser.add_argument('--na-value', action='store', dest='na_value', type=int, default=None,
                    help='A numeric value to use when a value is n/a. Defaults to None. Also configurable per column.')
parser.add_argument('--days', action='store_true',
                    help="Generate output column transforming date column to days since 1 Jan 1970.")
parser.add_argument('--age', action='store_true',
                    help="Generate output column transforming date column to days since date value.")
# TODO: parser.add_argument('--continuous', action='store_true',
#                           help="Generate continuous variables for columns that support it.")
# TODO: parser.add_argument('--scaling', action='store_true',
#                           help="Min/max scaling for variables to 0 to 1 range.")

# configuration management
parser.add_argument('--download', action='store_true',
                    help="Download datafiles that are not present. No processing or output with this option.")
parser.add_argument('--force', action='store_true',
                    help="Download datafiles even if present and overwrite (with --download).")
parser.add_argument('--counts', action='store_true',
                    help="Generate unique value counts for columns configured for mapping and ranking.")
parser.add_argument('--generate-config', action='store_true', dest='generate_config',
                    help="Generate templates for config.yml, dictionary.csv, and mapping.csv.")

# output control
parser.add_argument('--sources',
                    help="Comma-delimited list of sources to include based on 'name' in each 'config.yml'.",
                    type=lambda src: [item for item in src.split(',')])  # validate against configured sources
parser.add_argument('--columns',
                    help="Comma-delimited list of columns to include based on 'column' in *.dict files.",
                    type=lambda src: [item for item in src.split(',')])  # validate against configured dictionaries
parser.add_argument('--output',  action='store', type=str, default='output.csv',
                    help='The desired output file name.')
parser.add_argument('--individual',  action='store_true',
                    help='Generate intermediate output file for each source.')
parser.add_argument('--join',  action='store_true',
                    help='Generate merged output file for sources specified in --sources.')
parser.add_argument('--variant',  action='store', type=str,
                    help='Filter to a specific variant/allele (CV VariationID). Variable must be tagged in join-group.')
parser.add_argument('--gene',  action='store', type=str,
                    help='Filter to a specific gene (symbol). Variable must be tagged in join-group.')

args = parser.parse_args()

if args.join and not args.sources:
    print("ERROR: must specify --sources when specifying --join. The sources list is the list of data sources to join.")
    exit(-1)

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

####################
#
# Logging setup
#
####################
numeric_level = getattr(logging, args.loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % args.loglevel)
logging.basicConfig(filename='python.log', encoding='utf-8', level=numeric_level)


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


# constants
one_hot_prefix = 'hot'
categories_prefix = 'cat'
ordinal_prefix = 'ord'
rank_prefix = 'rnk'
days_prefix = 'days'
age_prefix = 'age'
sources_path = './sources'

# if multiple joins are possible, choose highest precedence join column
join_precedence = ('variation-id', 'gene-symbol', 'hgnc-id')

pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.options.mode.copy_on_write = True  # will become default in Pandas 3


###############################
#
# GENERATE CONFIGURATION YML
#
###############################
config_yml = """--- # Source file description
- name: source-name # usually directory name
  url: # put download url here (e.g. https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz)
  download_file: # put name of download file here if different from final file name (e.g. for gz first) (optional)
  file: data.tsv # put name of download file here (if gzip then put the final unzipped name here)
  gzip: 0 # 0 = no gzip, 1 = use gunzip to transform download_file to file
  header_row: 0 # the row number in file that contains the column headers starting at row zero for first line
  skip_rows: None # comma separated list of rows to skip starting at 0 before the header (header 0 after skipped rows)
  delimiter: tab # tab or csv delimited?
  quoting: 0 # Pandas read_csv quoting strategy {0 = QUOTE_MINIMAL, 1 = QUOTE_ALL, 2 = QUOTE_NONNUMERIC, 3 = QUOTE_NONE}
  strip_hash: 1 # Whether to strip leading hash(#) from column names (1=strip, 0=don't)
  md5_url: # Download url for md5 checksum file (optional)
  md5_file: # Name of md5 checksum file to download (optional)
  template: # Text template which can generate a new output column. Template fields {column name} use dictionary names.
"""
if args.generate_config:
    cnt = 0
    for root, dirs, files in os.walk(sources_path):
        for d in dirs:
            yml = '{}/{}/{}'.format(sources_path, d, 'config.yml')
            if isfile(yml) and access(yml, R_OK):
                debug("Found existing config.yml", yml)
            else:
                cnt = cnt + 1
                debug("Need to create", yml)
                with open(yml, 'w') as file:
                    file.write(config_yml)
    if args.info:
        if cnt == 0:
            info("All data sources have a config.yml")
        else:
            info("Created", cnt, "config.yml files.")

#########################
#
# LOAD SOURCE CONFIGURATION
#
#########################

# find and create a list of all the config.yml files
configList = []
for root, dirs, files in os.walk(sources_path):
    for f in files:
        if f == 'config.yml':
            file = '{}/{}/{}'.format(sources_path, os.path.basename(root), f)
            configList += [file]
            debug(file)

debug("config file list:")
debug(configList)

# load all the config files into a source list dataframe
sourcefiles = pd.DataFrame(columns=['name', 'path', 'url', 'download_file', 'file', 'gzip', 'header_row',
                                    'skip_rows', 'delimiter', 'quoting', 'strip_hash', 'md5_url', 'md5_file',
                                    'template'])

for c in configList:
    debug("for c in configList: c=", str(c))
    path = c.replace('/config.yml', '')  # path is everything but trailing /config.yml
    debug("for c in configList: path=", path)
    with open(c, "r") as stream:
        try:
            config = yaml.safe_load(stream)[0]
            debug("config:", str(c))
            debug(config)
            # add to config dataframe
            sourcefiles.loc[len(sourcefiles)] = [
                config.get('name'), path, config.get('url'), config.get('download_file'),
                config.get('file'), config.get('gzip'), config.get('header_row'),
                config.get('skip_rows'), config.get('delimiter'), config.get('quoting'),
                config.get('strip_hash'), config.get('md5_url'), config.get('md5_file'),
                config.get('template')
            ]

        except yaml.YAMLError as exc:
            critical(exc)
            exit(-1)

# annotate source list with helper columns
sourcefiles['dictionary'] = sourcefiles.apply(lambda x: 'dictionary.csv', axis=1)
sourcefiles['mapping'] = sourcefiles.apply(lambda x: 'mapping.csv', axis=1)

sourcefiles.set_index('name')

debug(sourcefiles)


#########################
#
# SOURCE LIST FILTRATION
#
#########################

# validate sourcefile selections in arguments if any
if args.sources is None:
    sources = list(set(sourcefiles['name']))
else:
    sources = list(set(sourcefiles['name']) & set(args.sources))

# any invalid sources?
invsources = set(sources).difference(sourcefiles['name'])
if len(invsources) > 0:
    error("Invalid source file specficied in --sources parameter: ", invsources)
    exit(-1)

debug("Using source files: ", sources)

# restrict source list by command line option, if any
if args.sources:
    sourcefiles = sourcefiles.loc[sourcefiles['name'].isin(sources)]

debug("Source configurations: ", sourcefiles)


#########################
#
# DOWNLOAD DATA FILES
#
#########################

download_count = 0
for i, s in sourcefiles.iterrows():
    name = s.get('name')
    source_path = s.get('path')
    download_file = s.get('download_file')
    download_file_path = ''
    if download_file:
        download_file_path = source_path + '/' + download_file
        debug("download_file specified for ", name, "as", download_file)
    md5_file = s.get('md5_file')
    md5_file_path = ''
    if md5_file:
        md5_file_path = source_path + '/' + md5_file
    datafile = s.get('file')
    datafile_path = ''
    if datafile:
        datafile_path = source_path + '/' + datafile
        debug("datafile specified for ", name, "as", datafile_path)
    # see if the file is present
    need_download = False
    if len(datafile_path) > 0:
        if args.force:
            need_download = True
        else:
            if isfile(datafile_path) and access(datafile_path, R_OK):
                debug("Found existing readable file", datafile_path)
            else:
                if args.download:
                    need_download = True
                else:
                    critical("ERROR: missing source file", datafile_path, "; specify --download to acquire.")
                    exit(-1)
    else:
        critical("No datafile specified for", name, "!")
        exit(-1)
    if need_download:
        if args.download:
            download_count = download_count + 1
            md5_hash_approved = ''
            md5_hash_downloaded = ''
            md5_url = s.get('md5_url')
            downloaded_file_path = ''
            url = s.get('url')
            if url:
                if download_file:
                    r = download(url, download_file_path)
                    downloaded_file_path = download_file_path
                else:
                    r = download(url, datafile_path)
                    downloaded_file_path = datafile_path
                if md5_url:  # if we are doing md5 check then get the hash for the downloaded file
                    md5_hash_downloaded = get_md5(downloaded_file_path)
                info("Completed data file download;", downloaded_file_path)
            else:
                warning("WARNING: no url for", datafile, "for", s.get('name'))
            if md5_url:
                if md5_file:
                    r = download(md5_url, md5_file_path)
                    md5_hash_approved = r.text.split(' ')
                    if md5_hash_downloaded in md5_hash_approved:
                        info("MD5 check successful")
                    else:
                        error("ERROR: MD5 check failed")
                        error("Approved:", md5_hash_approved)
                        error("Downloaded:", md5_hash_downloaded)
                        exit(-1)
                else:
                    warning("WARNING: md5_url specified but not md5_file. Not performing checksum.")
            gzip_flag = s.get('gzip')
            if gzip_flag:
                if datafile != download_file:  # for gzip datafile and download file should be different
                    gunzip_file(downloaded_file_path, datafile_path)
                else:
                    error("gzip option requires diffirng data/download file names for", name)
            # else:  if there's a future case where we need to change the name of a non-gzip downloaded file afterward

    else:
        debug("Data file", datafile, "already present.")

if args.download:
    info("Downloading complete;", download_count, "files.")
    exit(0)

#########################
#
# FIELD CONFIG DICTIONARY
#
#########################


def generate_dictionary(srcfile):
    # TODO: analyze column data and set category, onehot, continuous, days, age, based on data types and frequency
    print("Creating dictionary template")
    data_file = srcfile.get('path') + '/' + srcfile.get('file')
    separator_type = get_separator(srcfile.get('delimiter'))
    df_data_loc = pd.read_csv(data_file,
                              header=srcfile.get('header_row'), sep=separator_type,
                              skiprows=skip_array(srcfile.get('skip_rows')), engine='python',
                              quoting=srcfile.get('quoting'),
                              nrows=0,
                              on_bad_lines='warn')
    cols = df_data_loc.columns.tolist()
    # newcol = column.strip(' #')
    # create dataframe with appropriate columns
    df_dic = pd.DataFrame(columns=['column', 'comment', 'join-group', 'onehot', 'category',
                                   'continuous', 'format', 'map', 'days', 'age', 'expand', 'na-value'])
    # create one row per column header
    defaults = {'comment': '', 'join-group': '', 'onehot': 'FALSE', 'category': 'FALSE', 'continuous': 'FALSE',
                'format': '', 'map': 'FALSE', 'days': 'FALSE', 'age': 'FALSE', 'expand': 'FALSE', 'na-value': ''}
    for field in cols:
        df_dic.loc[len(df_dic)] = [field, defaults['comment'], defaults['join-group'], defaults['onehot'],
                                   defaults['category'], defaults['continuous'], defaults['format'], defaults['map'],
                                   defaults['days'], defaults['age'], defaults['expand']]
    # save dataframe as csv
    dictemplate = srcfile.get('path') + '/dictionary.csv'
    df_dic.to_csv(dictemplate, index=False)
    info("Created dictionary template", dictemplate)
    return ''


#  verify existence of source dictionaries
missing_dictionary = 0
for index, sourcefile in sourcefiles.iterrows():
    dictionary_file = sourcefile.get('path') + '/' + sourcefile.get('dictionary')
    if isfile(dictionary_file) and access(dictionary_file, R_OK):
        debug("Found dictionary file", dictionary_file)
    else:
        warning("WARNING: Missing dictionary file", dictionary_file)
        missing_dictionary = missing_dictionary + 1
        if args.generate_config:
            generate_dictionary(sourcefile)

if missing_dictionary:
    if not args.generate_config:
        critical(missing_dictionary, "missing dictionaries.",
                 "Use --generate-config to create template configurations.")
        exit(-1)
else:
    debug("Verified all dictionaries exist.")

# setup sources dictionary
dictionary = pd.DataFrame(columns=['name', 'path', 'file', 'column', 'comment', 'join-group', 'onehot', 'category',
                                   'continuous', 'format', 'map', 'days', 'age', 'expand', 'na-value'])
data = dict()
global sourcecolumns, map_config_df

#  process each source file and dictionary
for index, sourcefile in sourcefiles.iterrows():

    debug(sourcefile.get('path'), sourcefile.get('file'),
          sourcefile.get('dictionary'), "sep='" + sourcefile.get('delimiter') + "'")

    separator = get_separator(sourcefile.get('delimiter'))

    # read source dictionary
    debug("Reading dictionary")
    debug("sourcefile =", sourcefile)

    dictionary_file = sourcefile.get('path') + '/' + sourcefile.get('dictionary')

    info("Read dictionary", dictionary_file)

    dic = pd.read_csv(dictionary_file)

    debug(dic)

    # add dictionary entries to global dic if specified on command line, or all if no columns specified on command line
    for i, r in dic.iterrows():
        if args.columns is None or r['column'] in args.columns:
            dictionary.loc[len(dictionary)] = [sourcefile.get('name'),
                                               sourcefile.get('path'), sourcefile.get('file'), r.get('column'),
                                               r.get('comment'), r.get('join-group'), r.get('onehot'),
                                               r.get('category'), r.get('continuous'), r.get('format'), r.get('map'),
                                               r.get('days'), r.get('age'), r.get('expand'), r.get('na-value')]

    debug("Dictionary processed")

    # read source sources
    info("Reading source for", sourcefile.get('name'), "...")

    sourcefile_file = sourcefile.get('path') + '/' + sourcefile.get('file')

    if args.columns is None:
        df_tmp = pd.read_csv(sourcefile_file,
                             header=sourcefile.get('header_row'), sep=separator,
                             skiprows=skip_array(sourcefile.get('skip_rows')), engine='python',
                             quoting=sourcefile.get('quoting'),
                             # nrows=100,
                             on_bad_lines='warn')
        debug("File header contains columns:", df_tmp.columns)
        data.update({sourcefile['name']: df_tmp})
        sourcecolumns = list(set(dic['column']))
    else:
        sourcecolumns = list(set(dic['column']) & set(args.columns))
        data.update({sourcefile['name']: pd.read_csv(sourcefile_file,
                                                     #  usecols=sourcecolumns,
                                                     usecols=lambda x: x.strip(' #') in sourcecolumns,
                                                     header=sourcefile.get('header_row'), sep=separator,
                                                     skiprows=skip_array(sourcefile.get('skip_rows')), engine='python',
                                                     quoting=sourcefile.get('quoting'),
                                                     # nrows=100,
                                                     on_bad_lines='warn')})
    if sourcefile['strip_hash'] == 1:
        debug("Strip hashes and spaces from column labels")
        df = data[sourcefile.get('name')]
        # rename columns
        for column in df:
            newcol = column.strip(' #')
            if newcol != column:
                debug("Stripping", column, "to", newcol)
                data[sourcefile['name']] = df.rename({column: newcol}, axis='columns')
            else:
                debug("Not stripping colum", column)
        debug(data[sourcefile['name']])
    else:
        debug("Not stripping column labels")

    if args.expand:
        debug("name:", sourcefile['name'])
        debug("dictionary:")
        debug(dic)
        dic_filter_df = dic.loc[(dic.get('expand') == True)]
        if len(dic_filter_df) > 0:
            debug("Found", len(dic_filter_df), "columns to expand.")
            sourcename = sourcefile.get('name')
            df = data[sourcefile.get('name')]
            debug("expand columns for", sourcename, "length", len(df))
            for i, r in dic_filter_df.iterrows():
                col_name = r['column']
                debug("expanding column", col_name)
                expandable_rows_df = df.loc[(df.get(col_name).str.contains(","))]
                # for each row, create a copy with each value
                for exp_i, exp_r in expandable_rows_df.iterrows():
                    values = exp_r[col_name].split(",")
                    for v in values:
                        new_row = expandable_rows_df.loc[exp_i].copy()
                        new_row[col_name] = v
                        df.loc[len(df)] = new_row
            debug("new length", len(df))
            data[sourcename] = df

    # is there an optimal spot to filter for gene and variant?
    if args.gene:
        debug("filter genes", args.gene)
        dic_filter_df = dic.loc[(dic['join-group'] == 'gene-symbol')]
        if len(dic_filter_df) > 0:
            df = data[sourcefile['name']]
            debug("filter columns with gene-symbol join group and value", args.gene,
                  "for", sourcefile['name'], "length", len(df))
            for i, r in dic_filter_df.iterrows():
                col_name = r['column']
                genes = args.gene.split(',')
                debug("filtering column", col_name, " in ", genes)
                df = df.loc[(df[col_name].isin(genes))]
            debug("new length", len(df))
            data[sourcefile['name']] = df

    if args.variant:
        debug("filter variant", args.variant)
        dic_filter_df = dic.loc[(dic['join-group'] == 'variation-id')]
        if len(dic_filter_df) > 0:
            df = data[sourcefile['name']]
            debug("filter columns with variation-id join group and value", args.variant,
                  "for", sourcefile['name'], "length", len(df))
            for i, r in dic_filter_df.iterrows():
                col_name = r['column']
                variants = map(int, args.variant.split(','))
                debug("filtering column", col_name, " = ", args.variant, variants)
                df = df.loc[df[col_name].isin(variants)]
            debug("new length", len(df))
            data[sourcefile['name']] = df

    # show count of unique values per column
    if args.counts:
        print(sourcefile['name'], ":", data[sourcefile['name']].nunique())
        print("Finshed reading source file")
        print()
        print()

    # read mapping file, if any, and filter by selected columns, if any
    mapping_file = sourcefile['path'] + '/' + 'mapping.csv'
    map_config_df = pd.DataFrame()
    if not args.generate_config:
        map_config_df = pd.read_csv(mapping_file)
        map_config_df = map_config_df.loc[map_config_df['column'].isin(sourcecolumns)]

        debug("Mapping Config:", map_config_df)

    # for rank and group mapping columns, show the counts of each value
    if args.counts:
        # loop through each column that has rank and/or group set to True
        # sourcecolumns has list of columns to sift through for settings
        if args.generate_config:
            # create map configs dataframe to collect the values
            map_config_df = pd.DataFrame(
                columns=['column', 'value', 'frequency', 'map-name', 'map-value']
            )
        df = data[sourcefile['name']]
        for i, r in dic.iterrows():
            if r['map'] is True:
                print()
                print("unique values and counts for", sourcefile['path'], sourcefile['file'], r['column'])
                value_counts_df = df[r['column']].value_counts().rename_axis('value').reset_index(name='count')
                debug(df)
                debug(value_counts_df)
                if args.counts:
                    print(value_counts_df)

                if args.generate_config:
                    # add to the map configs dataframe
                    debug("generate configs for mapping/ranking for", r['column'])
                    for ind, row in value_counts_df.iterrows():
                        map_config_df.loc[len(map_config_df)] = [r['column'], row['value'], row['count'], '', '']
        if args.generate_config:
            # save the map configs dataframe as a "map-template" file in the source file directory
            map_config_df.to_csv(mapping_file + '.template', index=False)

    # create augmented columns for onehot, mapping, continuous, scaling, categories, rank
    if args.onehot or args.categories or args.map:  # or args.continuous or args.scaling

        df = data[sourcefile['name']]
        debug("Processing onehot, mapping, etc. for", sourcefile['name'], "df=", df)

        # loop through each column and process any configured options
        # for i, r in dictionary.iterrows():
        for i, r in dic.iterrows():

            column_name = r['column']

            #
            # mappings
            #
            if args.map and r['map'] is True:

                # get mapping subset for this column, if any (dictionary column name == mapping column name)
                map_col_df = map_config_df.loc[map_config_df['column'] == column_name]
                map_col_df = map_col_df.drop(columns={'column', 'frequency'}, axis=1)
                map_col_df.rename(columns={'value': column_name}, inplace=True)

                debug("Map config for column:", column_name)
                debug(map_col_df)

                # get list of unique 'map-name' values
                map_names = map_col_df['map-name'].unique()

                # loop through each 'map-name'
                if len(map_names) > 0 and len(map_col_df.index) > 0:

                    for m in map_names:

                        # create filtered dataframe for map-name
                        map_name_df = map_col_df.loc[(map_col_df['map-name'] == m)]
                        map_name_df = map_name_df.drop(columns={'map-name'}, axis=1)

                        # rename map-value as the value of map-name in the sub-filtered dataframe
                        map_name_df.rename(columns={'map-value': m}, inplace=True)

                        # merge based on column-name
                        df[column_name] = df[column_name].astype(str)
                        map_name_df[column_name] = map_name_df[column_name].astype(str)
                        df = pd.merge(
                            left=df,
                            right=map_name_df,
                            left_on=column_name,
                            right_on=column_name,
                            how='left',
                            suffixes=(None, '_remove')
                        )
                        # get rid of duplicated columns from join
                        df.drop(df.filter(regex='_remove$').columns, axis=1, inplace=True)

            #
            # onehot encoding
            #
            if args.onehot and r['onehot'] is True:
                debug("One-hot encoding", column_name, "as", one_hot_prefix+column_name)
                oh_prefix = column_name + '_' + one_hot_prefix + '_'
                one_hot_encoded = pd.get_dummies(df[column_name], prefix=oh_prefix)
                df = pd.concat([df, one_hot_encoded], axis=1)

            #
            # categories/label encoding
            #
            if args.categories and r['category'] is True:
                encoder = LabelEncoder()
                encoded_column_name = categories_prefix + '_' + column_name
                debug("Category encoding", column_name, "as", encoded_column_name)
                debug("Existing values to be encoded:", df)
                df[encoded_column_name] = encoder.fit_transform(df[column_name])

                # TODO: do we then normalize or scale the values afterwards, is that a separate option?

            # date time encodings (age, days)
            if not pd.isna(r['format']):
                debug("Age/Days: Column=", column_name, " format=", r['format'])
                if args.age:
                    age_column = age_prefix + '_' + column_name
                    df[age_column] = df.apply(lambda x: get_age(x.get(column_name), r['format']), axis=1)
                if args.days:
                    days_column = days_prefix + '_' + column_name
                    df[days_column] = df.apply(lambda x: get_days(x.get(column_name), r['format']), axis=1)

            # column-level NaN value replacement
            if not pd.isna(r['na-value']) and r['na-value'] is not None:
                debug("Apply na-value", r['na-value'], "to", column_name)
                df.fillna({column_name: r['na-value']}, inplace=True)

            # Strategies: variable deletion, mean/median imputation, most common value, ???
            # continuous
            #  z-score?
            #   (https://www.analyticsvidhya.com/blog/2015/11/8-ways-deal-continuous-variables-predictive-modeling/)
            #  log transformation
            #   (https://www.freecodecamp.org/news/feature-engineering-and-feature-selection-for-beginners/)
            # min-max Normalization
            #   (https://www.freecodecamp.org/news/feature-engineering-and-feature-selection-for-beginners/)
            # standardization
            #   (https://www.freecodecamp.org/news/feature-engineering-and-feature-selection-for-beginners/)

            # scaling

        # if specified, fill any remaining N/A values that weren't filled in at the field level
        if args.na_value is not None:
            df.fillna(args.na_value, inplace=True)

        # copy back to our data array
        data[sourcefile['name']] = df

    if args.template and len(sourcefile['template']) > 0:
        sourcefile_name = sourcefile['name']
        template_column_name = "{}-template".format(sourcefile_name)
        debug("Applying template to", sourcefile_name, "as", template_column_name)
        df = data[sourcefile_name]
        df[template_column_name] = df.apply(lambda x: apply_template(sourcefile['template'], x), axis=1)
        data[sourcefile_name] = df

    debug("Data:", data[sourcefile['name']])

# show the dictionary
debug("Columns:", args.columns)
debug("Dictionary:", dictionary)


#########################
#
# PER-SOURCE OUTPUT
#
#########################

# create per-source output files to debugging purposes
if args.individual:
    debug("sources.keys:", data.keys())
    debug("sourcefiles:", sourcefiles)

    # summarize our sources
    for d in data.keys():
        debug("columns for ", d, ":")
        debug(data[d].columns.values.tolist())

        # files put in current directory, prepend source name to file
        output_file = d + '-' + args.output
        debug("Generating intermediate source output", output_file)
        out_df = data[d]
        debug("out_df:", out_df)
        out_df.to_csv(output_file, index=False)


#########################
#
# MERGED OUTPUT
#
#########################

# merge selected source files by join-group
# only merge if sources specified on command line (--sources)
if args.join:
    if args.sources:
        # merge by order of sources specified on command line using left joins in sequence
        info("Merging data sources:", args.sources)
        sources_sort = list(args.sources)

        dic_df = dictionary[dictionary['join-group'].notnull()]
        dic_df['precedence'] = dic_df.apply(lambda x: get_join_precedence(x.get('join-group')), axis=1)
        out_df = pd.DataFrame()
        already_joined_dic_df = pd.DataFrame(data=None, columns=dictionary.columns)
        c = 0
        for s in sources_sort:
            info("Merging", s)
            # get join columns for s
            s_dic_df = dic_df.loc[(dic_df['name'] == s)].sort_values(by=['precedence'])
            # s_join_columns = filter dictionary by s and join-group not null
            if c == 0:
                out_df = data[s]
            else:
                # pick a join group that has already in a merged dataset, starting with the highest precedence
                join_groups = s_dic_df['join-group'].unique()
                debug("joins for", s, "include", join_groups)
                debug("prior join groups:", already_joined_dic_df)
                selected_join_group = None
                for jg in join_groups:
                    debug("checking if previous merges have", jg)
                    if len(already_joined_dic_df.loc[(already_joined_dic_df['join-group'] == jg)]) == 0:
                        continue
                    selected_join_group = jg
                    break
                if selected_join_group is None:
                    error("Didn't find a matching prior join-group for", s)
                    exit(-1)
                # get the left and right join column names for selected join group
                left_join_df = already_joined_dic_df.loc[(already_joined_dic_df['join-group']
                                                          == selected_join_group)].iloc[0]
                left_join_column = left_join_df['column']
                debug("Left join column", left_join_column)

                right_join_df = s_dic_df.loc[(s_dic_df['join-group'] == selected_join_group)].iloc[0]
                right_join_column = right_join_df['column']
                debug("Right join column", right_join_column)
                debug("Out length prior", len(out_df))
                out_df = pd.merge(out_df, data[s], how='left', left_on=left_join_column, right_on=right_join_column)
                debug("Out length after", len(out_df))
            c = c + 1
            debug("Adding to prior join df", s_dic_df)
            already_joined_dic_df = pd.concat([already_joined_dic_df, s_dic_df])
            debug("Now prior join df:")
            debug(already_joined_dic_df)

        # fill in any Nan values after merging dataframes
        if args.na_value is not None:
            out_df.fillna(args.na_value, inplace=True)

        output_file = args.output
        info("Generating output", output_file)
        debug("out_df:", out_df)
        out_df.to_csv(output_file, index=False)
    else:
        error("ERROR: --join requires at least one source specified with --sources parameter.")
        exit(-1)

info("Exiting")

exit(0)
