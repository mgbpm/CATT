from datetime import datetime, timezone
import pytz
import pandas as pd
import argparse
from sklearn.preprocessing import LabelEncoder
import os
import yaml
from os import access, R_OK
from os.path import isfile
import requests
import hashlib
import gzip
import shutil

# TODO:
#  ** look for missing or deprecated columns in data files as compared to dictionaries and mapping files
#    (e.g. recent addition of oncology data)
#    - does dictionary have all the columns, are dictionary columns all present in the file?
#    - are all mapping columns still present in the file?

# TODO:
#  ** when creating dictionary template: analyze column data and set category,
#       onehot, continuous, days, age, based on data types and frequency

# Tue Mar 10 00:00:00 UTC 2015
# Tue Mar 10 00:00:00 UTC 2015
# Wed Aug 24 00:00:00 UTC 2022
# Tue Mar 10 00:00:00 UTC 2015
# Mon Nov 02 21:15:11 UTC 2020
# %a %b %d %H:%M%S %Z %Y
#
# 2016-06-08T14:14:30Z
# %Y-%m-%dT%H:%M:%SZ
#
# 2018-06-07T16:00:00.000Z
# %Y-%m-%dT%H:%M:%S.%fZ
#
# Thu, 04 Apr 2019 16:27:31 -0000
# Thu, 04 Apr 2019 16:27:31 -0000
# Wed, 09 Feb 2022 13:14:39 -0000
# Thu, 04 Apr 2019 16:27:31 -0000
# Thu, 04 Apr 2019 00:00:00 -0000
# Wed, 01 Feb 2023 16:54:54 -0000
# Wed, 01 Feb 2023 00:00:00 -0000
# %a, %d %b %Y %H:%M:%S %z
#
# Mar 29, 2022
# Mar 23, 2023
# %b %d, %Y
#
# 2020-12-24
# %Y-%m-%d
#
# 2018-03-30 13:31:56
# 2020-06-18 13:31:17
# %Y-%m-%d %H:%M:%S
#
# datetime.strptime('31/01/22 23:59:59.999999',
#                   '%d/%m/%y %H:%M:%S.%f')
#
# Either keep a list of tokens for approved formats, or use the format string as the configuration


def str_to_datetime(date_str, date_format):
    dt = datetime.strptime(date_str, date_format).replace(tzinfo = pytz.UTC)
    return dt


epoch: datetime = str_to_datetime('01/01/1970', '%m/%d/%Y').replace(tzinfo = pytz.UTC)
today = datetime.now(timezone.utc)


def date_to_days(dt):
    return (dt-epoch).days


def date_to_age(dt):
    return (today-dt).days


def get_days(date_str, date_format):
    if date_str == "-":
        return -1
    dt = str_to_datetime(date_str, date_format)
    return date_to_days(dt)


def get_age(date_str, date_format):
    if date_str == "-":
        return -1
    dt = str_to_datetime(date_str, date_format)
    return date_to_age(dt)


def apply_template(template, record):
    # template is the string from the config.yml
    # record is the record array for one line of the source
    output = template
    for key, value in record.items():
        # substitute value for instances of {key} in template
        param = '{' + key + '}'
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
    if args.debug:
        print("Downoading", downloadurl, "as", filepath)
    req = requests.get(downloadurl)
    open(filepath, 'wb').write(req.content)
    if args.info:
        print("Completed download of", filepath)
    return req


def get_md5(filename_with_path):
    file_hash = hashlib.md5()
    with open(filename_with_path, "rb") as fp:
        while chunk := fp.read(8192):
            file_hash.update(chunk)
        if args.debug:
            print(file_hash.digest())
            print(file_hash.hexdigest())  # to get a printable str instead of bytes
    return file_hash.hexdigest()


def gunzip_file(fromfilepath, tofilepath):
    if args.debug:
        print("Ungzipping", fromfilepath, "to", tofilepath)
    with gzip.open(fromfilepath, 'rb') as f_in:
        with open(tofilepath, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    if args.info:
        print("Completed gunzip", tofilepath)


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
# debug/info
parser.add_argument('-d', '--debug', action='store_true', default=False,
                    help="Provide additional debugging and other information.")
parser.add_argument('-i', '--info', action='store_true',  default=False,
                    help="Provide progress and other information.")

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
parser.add_argument('-s', '--sources',
                    help="Comma-delimited list of sources to include based on 'name' in each 'config.yml'.",
                    type=lambda src: [item for item in src.split(',')])  # validate against configured sources
parser.add_argument('-c', '--columns',
                    help="Comma-delimited list of columns to include based on 'column' in *.dict files.",
                    type=lambda src: [item for item in src.split(',')])  # validate against configured dictionaries
parser.add_argument('-o', '--output',  action='store', type=str, default='output.csv',
                    help='The desired output file name.')
parser.add_argument('--individual',  action='store_true',
                    help='Generate intermediate output file for each source.')
parser.add_argument('--join',  action='store_true',
                    help='Generate merged output file for sources specified in --sources.')
parser.add_argument('-v', '--variant',  action='store', type=str,
                    help='Filter to a specific variant/allele (CV VariationID). Variable must be tagged in join-group.')
parser.add_argument('-g', '--gene',  action='store', type=str,
                    help='Filter to a specific gene (symbol). Variable must be tagged in join-group.')


args = parser.parse_args()

if args.join and not args.sources:
    print("ERROR: must specify --sources when specifying --join. The sources list is the list of data sources to join.")
    exit(-1)

# source selection
# --sources="name1,name2,name3,..."
# column selection
# --columns="column1,column2,column3..."
# filters
# --filter="column=value"
# debug options
# --debug
# --info
# --check; validate input options, validate files exist, validate dictionaries complete


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
  template: # A text template which can generate a new output column. Template fields {column name} use dictionary names.
"""
if args.generate_config:
    cnt = 0
    for root, dirs, files in os.walk(sources_path):
        for d in dirs:
            yml = '{}/{}/{}'.format(sources_path, d, 'config.yml')
            if isfile(yml) and access(yml, R_OK):
                if args.debug:
                    print("Found existing config.yml", yml)
            else:
                cnt = cnt + 1
                if args.debug:
                    print("Need to create", yml)
                with open(yml, 'w') as file:
                    file.write(config_yml)
    if args.info:
        if cnt == 0:
            print("All data sources have a config.yml")
        else:
            print("Created", cnt, "config.yml files.")

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
            if args.debug:
                print(file)

if args.debug:
    print("config file list:")
    print(configList)

# load all the config files into a source list dataframe
sourcefiles = pd.DataFrame(columns=['name', 'path', 'url', 'download_file', 'file', 'gzip', 'header_row',
                                    'skip_rows', 'delimiter', 'quoting', 'strip_hash', 'md5_url', 'md5_file',
                                    'template'])

for c in configList:
    path = c.replace('/config.yml', '')  # path is everything but trailing /config.yml
    with open(c, "r") as stream:
        try:
            config = yaml.safe_load(stream)[0]
            if args.debug:
                print("config:", c)
                print(config)
                print()
            # add to config dataframe
            sourcefiles.loc[len(sourcefiles)] = [
                config.get('name'), path, config.get('url'), config.get('download_file'),
                config.get('file'), config.get('gzip'), config.get('header_row'),
                config.get('skip_rows'), config.get('delimiter'), config.get('quoting'),
                config.get('strip_hash'), config.get('md5_url'), config.get('md5_file'),
                config.get('template')
            ]

        except yaml.YAMLError as exc:
            print(exc)
            exit(-1)

# annotate source list with helper columns
sourcefiles['dictionary'] = sourcefiles.apply(lambda x: 'dictionary.csv', axis=1)
sourcefiles['mapping'] = sourcefiles.apply(lambda x: 'mapping.csv', axis=1)

sourcefiles.set_index('name')

if args.debug:
    print(sourcefiles)


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
    print("Invalid source file specficied in --sources parameter: ", invsources)
    exit(-1)

if args.debug:
    print("Using source files: ", sources)

# restrict source list by command line option, if any
if args.sources:
    sourcefiles = sourcefiles.loc[sourcefiles['name'].isin(sources)]

if args.debug:
    print("Source configurations: ", sourcefiles)


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
        if args.debug:
            print("download_file specified for ", name, "as", download_file)
    md5_file = s.get('md5_file')
    md5_file_path = ''
    if md5_file:
        md5_file_path = source_path + '/' + md5_file
    datafile = s.get('file')
    datafile_path = ''
    if datafile:
        datafile_path = source_path + '/' + datafile
        if args.debug:
            print("datafile specified for ", name, "as", datafile_path)
    # see if the file is present
    need_download = False
    if len(datafile_path) > 0:
        if args.force:
            need_download = True
        else:
            if isfile(datafile_path) and access(datafile_path, R_OK):
                if args.debug:
                    print("Found existing readable file", datafile_path)
            else:
                if args.download:
                    need_download = True
                else:
                    print("ERROR: missing source file", datafile_path, "; specify --download to acquire.")
                    exit(-1)
    else:
        print("No datafile specified for", name, "!")
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
                print("Completed data file download;", downloaded_file_path)
            else:
                print("WARNING: no url for", datafile, "for", s.get('name'))
            if md5_url:
                if md5_file:
                    r = download(md5_url, md5_file_path)
                    md5_hash_approved = r.text.split(' ')
                    if md5_hash_downloaded in md5_hash_approved:
                        print("MD5 check successful")
                    else:
                        print("ERROR: MD5 check failed")
                        print("Approved:", md5_hash_approved)
                        print("Downloaded:", md5_hash_downloaded)
                        exit(-1)
                else:
                    print("WARNING: md5_url specified but not md5_file. Not performing checksum.")
            gzip_flag = s.get('gzip')
            if gzip_flag:
                if datafile != download_file:  # for gzip datafile and download file should be different
                    gunzip_file(downloaded_file_path, datafile_path)
                else:
                    print("ERROR: gzip option requires different data and download file names; check config for", name)
            # else:  if there's a future case where we need to change the name of a non-gzip downloaded file afterward

    else:
        if args.debug:
            print("Data file", datafile, "already present.")

if args.download:
    print("Downloading complete;", download_count, "files.")
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
    df_data = pd.read_csv(data_file,
                          header=srcfile.get('header_row'), sep=separator_type,
                          skiprows=srcfile.get('skip_rows'), engine='python',
                          quoting=srcfile.get('quoting'),
                          nrows=0,
                          on_bad_lines='warn')
    cols = df_data.columns.tolist()
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
    print("Created dictionary template", dictemplate)
    return ''


#  verify existence of source dictionaries
missing_dictionary = 0
for index, sourcefile in sourcefiles.iterrows():
    dictionary_file = sourcefile.get('path') + '/' + sourcefile.get('dictionary')
    if isfile(dictionary_file) and access(dictionary_file, R_OK):
        if args.debug:
            print("Found dictionary file", dictionary_file)
    else:
        print("WARNING: Missing dictionary file", dictionary_file)
        missing_dictionary = missing_dictionary + 1
        if args.generate_config:
            generate_dictionary(sourcefile)

if missing_dictionary:
    if not args.generate_config:
        print(missing_dictionary, "missing dictionaries. Use --generate-config to create template configurations.")
        exit(-1)
else:
    if args.debug:
        print("Verified all dictionaries exist.")

# setup sources dictionary
dictionary = pd.DataFrame(columns=['name', 'path', 'file', 'column', 'comment', 'join-group', 'onehot', 'category',
                                   'continuous', 'format', 'map', 'days', 'age', 'expand', 'na-value'])
data = dict()
global sourcecolumns, map_config_df

#  process each source file and dictionary
for index, sourcefile in sourcefiles.iterrows():

    if args.debug:
        print(sourcefile.get('path'), sourcefile.get('file'),
              sourcefile.get('dictionary'), "sep='" + sourcefile.get('delimiter') + "'")

    separator = get_separator(sourcefile.get('delimiter'))

    # read source dictionary
    if args.debug:
        print("Reading dictionary")

    if args.debug:
        print("sourcefile =", sourcefile)

    dictionary_file = sourcefile.get('path') + '/' + sourcefile.get('dictionary')

    if args.info:
        print("Read dictionary", dictionary_file)

    dic = pd.read_csv(dictionary_file)

    if args.debug:
        print(dic)

    # add dictionary entries to global dic if specified on command line, or all if no columns specified on command line
    for i, r in dic.iterrows():
        if args.columns is None or r['column'] in args.columns:
            dictionary.loc[len(dictionary)] = [sourcefile.get('name'),
                                               sourcefile.get('path'), sourcefile.get('file'), r.get('column'),
                                               r.get('comment'), r.get('join-group'), r.get('onehot'),
                                               r.get('category'), r.get('continuous'), r.get('format'), r.get('map'),
                                               r.get('days'), r.get('age'), r.get('expand'), r.get('na-value')]

    if args.debug:
        print("Dictionary processed")

    # read source sources
    if args.info:
        print("Reading source for", sourcefile.get('name'), "...")

    sourcefile_file = sourcefile.get('path') + '/' + sourcefile.get('file')

    if args.columns is None:
        df_tmp = pd.read_csv(sourcefile_file,
                             header=sourcefile.get('header_row'), sep=separator,
                             skiprows=skip_array(sourcefile.get('skip_rows')), engine='python',
                             quoting=sourcefile.get('quoting'),
                             # nrows=100,
                             on_bad_lines='warn')
        if args.debug:
            print("File header contains columns:", df_tmp.columns)
        data.update({sourcefile['name']: df_tmp})
        # data.update({sourcefile['name']: pd.read_csv(sourcefile_file,
        #                                              header=sourcefile.get('header_row'), sep=separator,
        #                                              skiprows=sourcefile.get('skip_rows'), engine='python',
        #                                              quoting=sourcefile.get('quoting'),
        #                                              nrows=100,
        #                                              on_bad_lines='warn')})
        sourcecolumns = list(set(dic['column']))
    else:
        sourcecolumns = list(set(dic['column']) & set(args.columns))
        data.update({sourcefile['name']: pd.read_csv(sourcefile_file,
                                                     #  usecols=sourcecolumns,
                                                     usecols=lambda x: x.strip(' #') in sourcecolumns,
                                                     header=sourcefile.get('header_row'), sep=separator,
                                                     skiprows=sourcefile.get('skip_rows'), engine='python',
                                                     quoting=sourcefile.get('quoting'),
                                                     # nrows=100,
                                                     on_bad_lines='warn')})
    if sourcefile['strip_hash'] == 1:
        if args.debug:
            print("Strip hashes and spaces from column labels")
        df = data[sourcefile['name']]
        # rename columns
        for column in df:
            newcol = column.strip(' #')
            if newcol != column:
                if args.debug:
                    print("Stripping", column, "to", newcol)
                data[sourcefile['name']] = df.rename({column: newcol}, axis='columns')
            else:
                if args.debug:
                    print("Not stripping colum", column)
        if args.debug:
            print(data[sourcefile['name']])
    else:
        if args.debug:
            print("Not stripping column labels")

    if args.expand:
        if args.debug:
            print("name:", sourcefile['name'])
            print("dictionary:")
            print(dic)
        dic_filter_df = dic.loc[(dic.get('expand') == True)]
        if len(dic_filter_df) > 0:
            df = data[sourcefile['name']]
            if args.debug:
                print("expand columns for", sourcefile['name'], "length", len(df))
            for i, r in dic_filter_df.iterrows():
                col_name = r['column']
                if args.debug:
                    print("expanding column", col_name)
                expandable_rows_df = df[df[col_name].str.contains(",")]
                # for each row, create a copy with each value
                for exp_i, exp_r in expandable_rows_df.iterrows():
                    values = exp_r[col_name].split(",")
                    for v in values:
                        new_row = expandable_rows_df.loc[exp_i].copy()
                        new_row[col_name] = v
                        df.loc[len(df)] = new_row
            if args.debug:
                print("new length", len(df))
            data[sourcefile['name']] = df

    # is there an optimal spot to filter for gene and variant?
    if args.gene:
        if args.debug:
            print("filter genes", args.gene)
        dic_filter_df = dic.loc[(dic['join-group'] == 'gene-symbol')]
        if len(dic_filter_df) > 0:
            df = data[sourcefile['name']]
            if args.debug:
                print("filter columns with gene-symbol join group and value", args.gene,
                      "for", sourcefile['name'], "length", len(df))
            for i, r in dic_filter_df.iterrows():
                col_name = r['column']
                genes = args.gene.split(',')
                if args.debug:
                    print("filtering column", col_name, " in ", genes)
                df = df.loc[(df[col_name].isin(genes))]
            if args.debug:
                print("new length", len(df))
            data[sourcefile['name']] = df

    if args.variant:
        if args.debug:
            print("filter variant", args.variant)
        dic_filter_df = dic.loc[(dic['join-group'] == 'variation-id')]
        if len(dic_filter_df) > 0:
            df = data[sourcefile['name']]
            if args.debug:
                print("filter columns with variation-id join group and value", args.variant,
                      "for", sourcefile['name'], "length", len(df))
            for i, r in dic_filter_df.iterrows():
                col_name = r['column']
                variants = map(int, args.variant.split(','))
                if args.debug:
                    print("filtering column", col_name, " = ", args.variant, variants)
                df = df.loc[df[col_name].isin(variants)]
            if args.debug:
                print("new length", len(df))
            data[sourcefile['name']] = df

    # show count of unique values per column
    if args.debug and args.counts:
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

        if args.debug:
            print("Mapping Config:", map_config_df)

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
                if args.debug:
                    print(df)
                if args.debug or args.counts:
                    print(value_counts_df)
                if args.generate_config:
                    # add to the map configs dataframe
                    if args.debug:
                        print("generate configs for mapping/ranking for", r['column'])
                    for ind, row in value_counts_df.iterrows():
                        map_config_df.loc[len(map_config_df)] = [r['column'], row['value'], row['count'], '', '']
        if args.generate_config:
            # save the map configs dataframe as a "map-template" file in the source file directory
            map_config_df.to_csv(mapping_file + '.template', index=False)

    # create augmented columns for onehot, mapping, continuous, scaling, categories, rank
    if args.onehot or args.categories or args.map:  # or args.continuous or args.scaling

        df = data[sourcefile['name']]
        if args.debug:
            print("Processing onehot, mapping, etc. for", sourcefile['name'], "df=", df)

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

                if args.debug:
                    print("Map config for column:", column_name)
                    print(map_col_df)

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
                if args.debug:
                    print("One-hot encoding", column_name, "as", one_hot_prefix+column_name)
                oh_prefix = column_name + '_' + one_hot_prefix + '_'
                one_hot_encoded = pd.get_dummies(df[column_name], prefix=oh_prefix)
                df = pd.concat([df, one_hot_encoded], axis=1)

            #
            # categories/label encoding
            #
            if args.categories and r['category'] is True:
                encoder = LabelEncoder()
                encoded_column_name = categories_prefix + '_' + column_name
                if args.debug:
                    print("Category encoding", column_name, "as", encoded_column_name)
                    print("Existing values to be encoded:", df)
                df[encoded_column_name] = encoder.fit_transform(df[column_name])

                # TODO: do we then normalize or scale the values afterwards, is that a separate option?

            # date time encodings (age, days)
            if not pd.isna(r['format']):
                if args.debug:
                    print("Age/Days: Column=", column_name, " format=", r['format'])
                if args.age:
                    age_column = age_prefix + '_' + column_name
                    df[age_column] = df.apply(lambda x: get_age(x.get(column_name), r['format']), axis=1)
                if args.days:
                    days_column = days_prefix + '_' + column_name
                    df[days_column] = df.apply(lambda x: get_days(x.get(column_name), r['format']), axis=1)

            # column-level NaN value replacement
            if r['na-value'] is not None:
                df[column_name].fillna(r['na-value'], inplace=True)


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
        if args.debug:
            print("Applying template to", sourcefile_name, "as", template_column_name)
        df = data[sourcefile_name]
        df[template_column_name] = df.apply(lambda x: apply_template(sourcefile['template'], x), axis=1)
        data[sourcefile_name] = df

    if args.debug:
        print("Data:", data[sourcefile['name']])

# show the dictionary
if args.debug:
    print("Columns:", args.columns)
    print("Dictionary:", dictionary)


#########################
#
# PER-SOURCE OUTPUT
#
#########################

# create per-source output files to debugging purposes
if args.individual:
    if args.debug:
        print("sources.keys:", data.keys())
        print("sourcefiles:", sourcefiles)
        print("sourcefiles['clingen-gene-disease']:", sourcefiles.loc[(sourcefiles['name'] == 'clingen-gene-disease')])
    # summarize our sources
    for d in data.keys():
        if args.debug:
            print("columns for ", d, ":")
            # print(sources[d].describe())
            print(data[d].columns.values.tolist())

        # files put in current directory, prepend source name to file
        output_file = d + '-' + args.output
        if args.debug:
            print("Generating intermediate source output", output_file)
        out_df = data[d]
        if args.debug:
            print("out_df:", out_df)
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
        if args.info or args.debug:
            print("Merging data sources:", args.sources)
        sources_sort = list(args.sources)

        dic_df = dictionary[dictionary['join-group'].notnull()]
        dic_df['precedence'] = dic_df.apply(lambda x: get_join_precedence(x.get('join-group')), axis=1)
        out_df = pd.DataFrame()
        already_joined_dic_df = pd.DataFrame(data=None, columns=dictionary.columns)
        c = 0
        for s in sources_sort:
            if args.info:
                print("Merging", s)
            # get join columns for s
            s_dic_df = dic_df.loc[(dic_df['name'] == s)].sort_values(by=['precedence'])
            # s_join_columns = filter dictionary by s and join-group not null
            if c == 0:
                out_df = data[s]
            else:
                # pick a join group that has already in a merged dataset, starting with the highest precedence
                join_groups = s_dic_df['join-group'].unique()
                if args.debug:
                    print("joins for", s, "include", join_groups)
                    print("prior join groups:", already_joined_dic_df)
                selected_join_group = None
                for jg in join_groups:
                    if args.debug:
                        print("checking if previous merges have", jg)
                    if (already_joined_dic_df['join-group'] == jg).any():
                        selected_join_group = jg
                        break
                if selected_join_group is None:
                    print("Didn't find a matching prior join-group for", s)
                    exit(-1)
                # get the left and right join column names for selected join group
                left_join_df = already_joined_dic_df.loc[(already_joined_dic_df['join-group']
                                                          == selected_join_group)].iloc[0]
                left_join_column = left_join_df['column']
                if args.debug:
                    print("Left join column", left_join_column)

                right_join_df = s_dic_df.loc[(s_dic_df['join-group'] == selected_join_group)].iloc[0]
                right_join_column = right_join_df['column']
                if args.debug:
                    print("Right join column", right_join_column)
                    print("Out length prior", len(out_df))
                out_df = pd.merge(out_df, data[s], how='left', left_on=left_join_column, right_on=right_join_column)
                if args.debug:
                    print("Out length after", len(out_df))
            c = c + 1
            if args.debug:
                print("Adding to prior join df", s_dic_df)
            already_joined_dic_df = pd.concat([already_joined_dic_df, s_dic_df])
            if args.debug:
                print("Now prior join df:")
                print(already_joined_dic_df)

        # fill in any Nan values after merging dataframes
        if args.na_value is not None:
            out_df.fillna(args.na_value, inplace=True)

        output_file = args.output
        if args.info:
            print("Generating output", output_file)
        if args.debug:
            print("out_df:", out_df)
        out_df.to_csv(output_file, index=False)
    else:
        print("ERROR: --join requires at least one source specified with --sources parameter.")
        exit(-1)

if args.info:
    print("Exiting")

exit(0)
