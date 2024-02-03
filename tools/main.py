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
#  ** generate templated output for use by LLMs

# TODO: geneOrVariant column somtimes contains a list of genes (or variants) (see clingen-overall-scores-pediatric)
#  ** Have to determine how to join on this column; do we split apart into multiple or join using a "contains" approach?

# TODO: refactor rank/group to allow mutliple groupings with configurable names
#  ** The name of the rank/group could be incorporated in the mapping file as a separate indexed field
#      1. create multiple "sets" when doing mutliple mappings for a column
#      2. add a new column to mapping.csv called "map-name" and remove the "rank" and "group" and replace
#      with "map-value". This will allow any number of mappings for the same column and map-name will become the
#      new column name when incorporated into the dataset with pd.merge.

# TODO:
#  ** look for missing or deprecated columns in data files as compared to dictionaries and mapping files
#    (e.g. recent addition of oncology data)
#    - does dictionary have all the columns, are dictionary columns all present in the file?
#    - are all mapping columns still present in the file?

# TODO:
#  ** when creating dictionary template: analyze column data and set category,
#       onehot, continuous, days, age, based on data types and frequency

# TODO:
#  ** investigate python template libraries for LLM text generation
#  ** add option to create txt output file based on a single AlleleID or
#       VariationID across files in a structured format appropriate for LLM

# TODO:
#  ** add a configuration for allowing n/a value choice, but also have a default
#  ** probably add as a dictionary configuration?
#  ** also add a general program flag for a default strategy?


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
    if args.info:
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
    if args.info:
        print("Ungzipping", fromfilepath, "to", tofilepath)
    with gzip.open(fromfilepath, 'rb') as f_in:
        with open(tofilepath, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    if args.info:
        print("Completed gunzip")


# constants
one_hot_prefix = 'hot'
categories_prefix = 'cat'
ordinal_prefix = 'ord'
rank_prefix = 'rnk'
sources_path = '../sources'

pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)


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
# TODO: parser.add_argument('--scaling', action='store_true', help="Min/max scaling for variables to 0 to 1 range.")
parser.add_argument('--onehot', action='store_true',
                    help="Generate one-hot encodings for columns that support it.")
parser.add_argument('--categories', action='store_true',
                    help="Generate category encodings for columns that support it.")
# TODO: parser.add_argument('--continuous', action='store_true',
#  help="Generate continuous variables for columns that support it.")
parser.add_argument('--map', action='store_true',
                    help="Generate new columns based on mapping group configuration.")

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
# TODO: parser.add_argument('-v', '--variant',  action='store', type=str, help='Filter to a specific variant/allele.')
# TODO: parser.add_argument('-g', '--gene',  action='store', type=str, help='Filter to a specific gene (symbol).')


args = parser.parse_args()

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
                cnt += 1
                if args.info:
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
                                    'skip_rows', 'delimiter', 'quoting', 'strip_hash', 'md5_url', 'md5_file'])

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
                config.get('strip_hash'), config.get('md5_url'), config.get('md5_file')
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
    sources = sourcefiles['name']
else:
    sources = list(set(sourcefiles['name']) & set(args.sources))

# any invalid sources?
invsources = set(sources).difference(sourcefiles['name'])
if len(invsources) > 0:
    print("Invalid source file specficied in --sources parameter: ", invsources)
    exit(-1)

if args.debug:
    print("Using source files: ", sources)

# restrict source list configuration by names
if args.sources:
    sourcefiles = sourcefiles.loc[sourcefiles['name'].isin(sources)]

if args.debug:
    print("Source configurations: ", sourcefiles)


#########################
#
# DOWNLOAD DATA FILES
#
#########################

# if url, get file
#   if download_file, move downloaded file to download_file (if not the same)
#   if file exists, move downloaded file to file (if not the same)
# if md5 url,
#   get md5 file
#   generate md5 of data file
#   compare to checksum file (error/exit if no match)
# if gzip
#   unzip download_file to file

# TODO: refactor to put if-download within the loop and instead verify all the datafiles?

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
            else:
                print("WARNING: no url for", datafile, "for", s.get('name'))
            print("Completed data file download")
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
                                   'continuous', 'text', 'map', 'days', 'age'])
    # create one row per column header
    defaults = {'comment': '', 'join-group': '', 'onehot': 'FALSE', 'category': 'FALSE', 'continuous': 'FALSE',
                'text': 'TRUE', 'map': 'FALSE', 'days': 'FALSE', 'age': 'FALSE'}
    for field in cols:
        df_dic.loc[len(df_dic)] = [field, defaults['comment'], defaults['join-group'], defaults['onehot'],
                                   defaults['category'], defaults['continuous'], defaults['text'], defaults['map'],
                                   defaults['days'], defaults['age']]
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
        missing_dictionary += 1
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
dictionary = pd.DataFrame(columns=['path', 'file', 'column', 'comment', 'join-group', 'onehot', 'category',
                                   'continuous', 'text', 'map', 'days', 'age'])
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
            dictionary.loc[len(dictionary)] = [sourcefile.get('path'), sourcefile.get('file'), r.get('column'),
                                               r.get('comment'), r.get('join-group'), r.get('onehot'),
                                               r.get('category'), r.get('continuous'), r.get('text'), r.get('map'),
                                               r.get('days'), r.get('age')]

    if args.debug:
        print("Dictionary processed")

    # read source sources
    if args.info:
        print("Reading source sources", sourcefile.get('name'), "...")

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
        if args.info:
            print(data[sourcefile['name']])
    else:
        if args.debug:
            print("Not stripping column labels")

    # show count of unique values per column
    if args.debug or args.counts:
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

        if args.info:
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
                        map_name_df = map_col_df.loc[map_col_df['map-name'] == m]
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
                one_hot_encoded = pd.get_dummies(df[r['column']], prefix=one_hot_prefix)
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

            # TODO: add a field level "missing" configuration to specify a strategy for handling missing sources
            # N/A, null, Empty, ?, none, empty, -, NaN, etc.
            # Strategies: variable deletion, mean/median imputation, most common value, ???

            # copy back to our data array
            data[sourcefile['name']] = df

    if args.info:
        print("Data:", data[sourcefile['name']])

# show the dictionary
if args.debug:
    print("Columns:", args.columns)
    print("Dictionary:", dictionary)


#########################
#
# GENERATE OUTPUT
#
#########################

# merge selected source files by join-group
# exit(0)
# try using merge to join sources
if args.debug:
    print("sources.keys:", data.keys())
    print("sourcefiles:", sourcefiles)
    print("sourcefiles['clingen-gene-disease']:", sourcefiles.loc[sourcefiles['name'] == 'clingen-gene-disease'])
# summarize our sources
for d in data.keys():
    if args.debug:
        print()
        print()
        print()
        print()
        print("columns for ", d, ":")
        # print(sources[d].describe())
        print(data[d].columns.values.tolist())

    # generate intermediate output files, one per source
    output_file = d + '-' + args.output
    if args.info:
        print("Generating intermediate source output", output_file)
    out_df = data[d]
    if args.debug:
        print("out_df:", out_df)
    out_df.to_csv(output_file, index=False)

    # TODO: ultimately we want a single file, not one per source so need to merge in this loop then output below

if args.info:
    print("Exiting")
exit(0)
# determine best configuration for pre-defining possible merges

print("Merging...")
merge1 = pd.merge(data['clinvar-variant-summary-summary'], data['clinvar-variant-summary-vrs'],
                  left_on='VariationID', right_on='clinvar_variation_id')
merge2 = pd.merge(merge1, data['gencc-submissions-submissions'],
                  left_on='GeneSymbol', right_on='gene_symbol')
merge3 = pd.merge(merge2, data['clingen-dosage-dosage'],
                  left_on='gene_symbol', right_on='GENE SYMBOL')
print()
print()
print("merge3:")
print(merge3.describe())
print(merge3.head())
print(merge3.columns.values.tolist())
print(merge3.size)
# gene
# variation id
# allele id

# determine best configuration for column selection
