# local modules
import helper

# other libraries
import os
from os import access, R_OK
from os.path import isfile
import pandas as pd

###############################
#
# GENERATE CONFIGURATION YML
#
# Scan ./sources directory and create config.yml for every source that does not have one
# using the below template.
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


def config(sources_path):
    cnt = 0
    for root, dirs, files in os.walk(sources_path):
        for d in dirs:
            yml = str(os.path.join(sources_path, d, 'config.yml'))

            if isfile(yml) and access(yml, R_OK):
                helper.debug("Found existing config.yml", yml)
            else:
                cnt = cnt + 1
                helper.debug("Created missing configuration ", yml, "; Please edit and re-run.")
                print("Created missing configuration ", yml, "; Please edit and re-run.")
                with open(yml, 'w') as file:
                    file.write(config_yml)
    if cnt == 0:
        helper.info("All data sources have a config.yml")
        print("All data sources have a config.yml")
    else:
        helper.info("Created", cnt, "config.yml files.")
        print("NOTICE: Created", cnt, "config.yml files. Please edit the file(s) and re-run.")
        exit(-1)

def dictionary(srcfile):
    # TODO: analyze column data and set category, onehot, continuous, days, age, based on data types and frequency
    print("Creating dictionary template")
    data_file = str(os.path.join(srcfile.get('path'), srcfile.get('file')))
    separator_type = helper.get_separator(srcfile.get('delimiter'))
    df_data_loc = pd.read_csv(data_file,
                              header=srcfile.get('header_row'), sep=separator_type,
                              skiprows=helper.skip_array(srcfile.get('skip_rows')), engine='python',
                              quoting=srcfile.get('quoting'),
                              nrows=0,
                              on_bad_lines='warn')
    cols = df_data_loc.columns.tolist()
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
    dictionary_template = str(os.path.join(srcfile.get('path'),'dictionary.csv'))
    df_dic.to_csv(dictionary_template, index=False)
    helper.info("Created dictionary template", dictionary_template)
    return ''


def mapping(mapping_file, data, sourcefile, dic):
    # loop through each column that has rank and/or group set to True
    # sourcecolumns has list of columns to sift through for settings
    # create map configs dataframe to collect the values
    helper.debug("Generate mapping file", mapping_file)
    map_config_df = pd.DataFrame(
        columns=['column', 'value', 'frequency', 'map-name', 'map-value']
    )
    df = data[sourcefile['name']]
    for i, r in dic.iterrows():
        if r['map'] is True:
            print()
            print("unique values and counts for", sourcefile['path'], sourcefile['file'], r['column'])
            value_counts_df = df[r['column']].value_counts().rename_axis('value').reset_index(name='count')
            helper.debug(df)
            helper.debug(value_counts_df)
            print(value_counts_df)

            # add to the map configs dataframe
            helper.debug("generate configs for mapping/ranking for", r['column'])
            for ind, row in value_counts_df.iterrows():
                map_config_df.loc[len(map_config_df)] = [r['column'], row['value'], row['count'], '', '']
    # save the map configs dataframe as a "map-template" file in the source file directory
    map_config_df.to_csv(mapping_file + '.template', index=False)