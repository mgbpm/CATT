import pandas as pd
import argparse
from sklearn.preprocessing import LabelEncoder

# TODO:
#  * investigate python template libraries for LLM text generation
#  * determine best way to configure "joins" of source files
#  * should I eliminate leading # on column names from ClinVar file? Maybe a "strip-comment" option?

# TODO HIGH PRIORITY
#  ** add clingen-actionability-all-assertions-adult file
#  ** add a configuration for allowing n/a value choice, but also have a default

# constants
one_hot_prefix = 'one'
categories_prefix = 'cat'
ordinal_prefix = 'ord'
rank_prefix = 'rnk'

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
parser.add_argument('--verbose', action='store_true', help="Provide additional debugging and other information.")

# encoding options
parser.add_argument('--scaling', action='store_true', help="Min/max scaling for variables to 0 to 1 range.")
parser.add_argument('--onehot', action='store_true', help="Generate one-hot encodings for columns that support it.")
parser.add_argument('--categories', action='store_true', help="Generate category encodings for columns that support it.")
parser.add_argument('--continuous', action='store_true', help="Generate continuous variables for columns that support it.")
parser.add_argument('--group', action='store_true', help="Generate new columns based on mapping group configuration.")
parser.add_argument('--rank', action='store_true', help="Generate new columns based on mapping rank configuration.")

# configuration management
parser.add_argument('--counts', action='store_true', help="Generate unique value counts for columns configured for mapping and ranking.")
parser.add_argument('--generate-config', action='store_true', dest='generate_config', help="Generate mapping and ranking templates (requires --counts).")

# output control
parser.add_argument('-s', '--sources', help="Comma-delimited list of sources to include based on 'name' in 'sources.csv'.",
    type=lambda s: [item for item in s.split(',')]) # validate below against configured sources
parser.add_argument('-c', '--columns', help="Comma-delimited list of columns to include based on 'column' in *.dict files.",
    type=lambda s: [item for item in s.split(',')]) # validate below against configured dictionaries
parser.add_argument( '-o', '--output',  action='store', type=str, default='output.csv', help = 'The desired output file name.' )


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

#########################
#
# CONFIGURATION
#
#########################

# read configuration dictionary
sourcefiles = pd.read_csv('../sources/sources.csv', sep=',', header=0, quotechar='"', engine='python')

# annotate source list with helper columns
sourcefiles['directory'] = sourcefiles.apply(lambda x: '../sources/' + x['name'], axis=1)
sourcefiles['dictionary'] = sourcefiles.apply(lambda x: 'dictionary.csv', axis=1)
sourcefiles['mapping'] = sourcefiles.apply(lambda x: 'mapping.csv', axis=1)

# validate sourcefile selections in arguments if any
if args.sources == None:
    sources = sourcefiles['name']
else:
    sources = list(set(sourcefiles['name']) & set(args.sources))

# any invalid sources?
invsources = set(sources).difference(sourcefiles['name'])
if len(invsources) > 0:
    print("Invalid source file specficied in --sources parameter: ", invsources)
    exit(-1)

if args.verbose:
    print("Using source files: ", sources)

# restrict source list configuration by names
if args.sources:
    sourcefiles = sourcefiles.loc[sourcefiles['name'].isin(sources)]

if args.verbose:
    print("Source configurations: ", sourcefiles)

# setup sources dictionary
dictionary = pd.DataFrame(columns=['directory', 'file', 'column', 'comment', 'onehot', 'category', 'continuous',
                                   'text', 'group', 'rank', 'days', 'age'])
data = dict()
global sourcecolumns, map_config_df

#  process each source file and dictionary
for index, sourcefile in sourcefiles.iterrows():

    if args.verbose:
        print(sourcefile['directory'], sourcefile['file'], sourcefile['dictionary'], "sep='" + sourcefile['delimiter'] + "'")

    delimiter = sourcefile['delimiter']
    if delimiter == 'tab':
        separator = '\t'
    elif delimiter == 'comma':
        separator = ','
    else:
        separator = None

    # read source dictionary
    if args.verbose:
        print("Reading dictionary")

    if args.verbose:
        print("sourcefile =", sourcefile)
    dictionary_file = sourcefile['directory'] + '/' + sourcefile['dictionary']

    if args.verbose:
        print("Read dictionary", dictionary_file)
    dic = pd.read_csv(dictionary_file)

    if args.verbose:
        print(dic)

    # add dictionary entries to global dic if specified on command line, or all if no columns specified on command line
    for i, r in dic.iterrows():
        if args.columns == None or r['column'] in args.columns:
            dictionary.loc[len(dictionary)] = [sourcefile['directory'], sourcefile['file'], r['column'], r['comment'], r['onehot'], r['category'], r['continuous'], r['text'], r['group'], r['rank'], r['days'], r['age']]

    if args.verbose:
        print("Dictionary processed")

    # read source sources
    if args.verbose:
        print("Reading source sources",sourcefile['name'],"...")

    sourcefile_file = sourcefile['directory'] + '/' + sourcefile['file']
    if args.columns == None:
        data.update({sourcefile['name']: pd.read_csv(sourcefile_file,
                                                     header=sourcefile['header_row'], sep=separator,
                                                     skiprows=sourcefile['skip_rows'], engine='python',
                                                     quoting=sourcefile['quoting'],
#                                                     nrows=100,
                                                     on_bad_lines='warn')})
        sourcecolumns = list(set(dic['column']))
    else:
        sourcecolumns = list(set(dic['column']) & set(args.columns))
        data.update({sourcefile['name']: pd.read_csv(sourcefile_file,
                                                     usecols=sourcecolumns,
                                                     header=sourcefile['header_row'], sep=separator,
                                                     skiprows=sourcefile['skip_rows'], engine='python',
                                                     quoting=sourcefile['quoting'],
#                                                     nrows=100,
                                                     on_bad_lines='warn')})
    if sourcefile['strip_hash'] == 1:
        print("Strip hashes and spaces from column labels")
        df = data[sourcefile['name']]
        #rename columns
        for column in df:
            newcol = column.strip(' #')
            if newcol != column:
                print("Stripping",column,"to",newcol)
                data[sourcefile['name']] = df.rename({column: newcol}, axis='columns')
            else:
                print("Not stripping colum", column)
        print(data[sourcefile['name']])
    else:
        print("Not stripping column labels")


    # show count of unique values per column
    if args.verbose:
        print(sourcefile['name'],":",
            data[sourcefile['name']].nunique()
            )
        print("Finshed reading source file")
        print()
        print()

    # read mapping file, if any, and filter by selected columns, if any
    mapping_file = sourcefile['directory'] + '/' + 'mapping.csv'
    map_config_df = pd.DataFrame()
    if not args.generate_config:
        map_config_df = pd.read_csv(mapping_file)
        map_config_df = map_config_df.loc[map_config_df['column'].isin(sourcecolumns)]

        if args.verbose:
            print("Mapping Config:",map_config_df)

    # for rank and group columns, show the counts of each value
    if args.counts:
        # loop through each column that has rank and/or group set to True
        # sourcecolumns has list of columns to sift through for settings
        if args.generate_config:
            # create map configs dataframe to collect the values
            map_config_df = pd.DataFrame(
                columns=['column','value','frequency','group','rank']
            )
        df = data[sourcefile['name']]
        for i, r in dic.iterrows():
            if r['group'] == True or r['rank'] == True:
                print()
                print("unique values and counts for",sourcefile['directory'],sourcefile['file'],r['column'])
                value_counts_df = df[r['column']].value_counts().rename_axis('value').reset_index(name='count')
                print(df)
                if args.verbose:
                    print(value_counts_df)
                    # show column names
                    print("column names for value_counts")
                    print(list(value_counts_df))
                if args.generate_config:
                    # add to the map configs dataframe
                    print("generate configs for mapping/ranking for",r['column'])
                    for index, row in value_counts_df.iterrows():
                        map_config_df.loc[len(map_config_df)] = [ r['column'], row['value'] ,row['count'], '', '' ]
        if args.generate_config:
            # save the map configs dataframe as a "map-template" file in the source file directory
            map_config_df.to_csv(mapping_file + '.template', index=False)


    # create augmented columns for onehot, mapping, continuous, scaling, categories
    if args.onehot or args.categories or args.continuous or args.scaling or args.group or args.rank:

        df = data[sourcefile['name']]

        # loop through each column and process any configured options
        for i, r in dictionary.iterrows():

            column_name = r['column']

            # get mapping subset for this column, if any (dictionary column name == mapping column name)
            map_col_df = map_config_df.loc[map_config_df['column'] == column_name]
            # rename columns for effective merging and output
            map_col_df = map_col_df.drop('column', axis=1)
            map_col_df.rename(columns={'value': column_name, 'group': column_name + '_grp', 'rank': column_name + '_rank'}, inplace=True)

            if args.verbose:
                print("Map config for column:",column_name)
                print(map_col_df)

            # onehot encoding
            if args.onehot and r['onehot'] == True:
                one_hot_encoded = pd.get_dummies(df[r['column']], prefix=one_hot_prefix)
                df = pd.concat([df, one_hot_encoded], axis=1)

            # categories/label encoding
            if args.categories and r['category'] == True:
                encoder = LabelEncoder()
                encoded_column_name = categories_prefix + '_' + column_name
                df[encoded_column_name] = encoder.fit_transform(df[column_name])

            # ordinal encoding
            if (args.rank and r['rank'] == True and len(map_col_df.index) > 0) or (args.group and r['group'] == True and len(map_col_df.index) > 0):
                encoded_column_name = rank_prefix + '_' + column_name
                # df[encoded_column_name] = df.apply(lambda row: map_col_df.loc[map_col_df['value'] == row[column_name], 'rank'], axis=1)
                df = pd.merge(
                    left=df,
                    right=map_col_df,
                    left_on=column_name,
                    right_on=column_name,
                    how='left',
                    suffixes=('','_'+column_name)
                )
                print("Not yet implemented")
                # TODO: should we use ranking as just the order, or use it as a numeric mapping?
                # TODO: do we then normalize or scale the values afterwards, is that a separate option?
                # mapping for column must be in mapping.csv file and include a rank value
                # get ranking values and ranks from mapping.csv
                # sources = {'Education': ['High School', 'Bachelor', 'Master', 'PhD', 'Bachelor']}
                # df = pd.DataFrame(sources)
                # education_order = ['High School', 'Bachelor', 'Master', 'PhD']
                # df['Education_OrdinalEncoded'] = df['Education'].apply(lambda x: education_order.index(x))
                # print(df)

            # mapping
            #if args.rank and r['rank'] == True:
            #    print("Not yet implemented")
            #    encoded_column_name = 'xxxx' # use "group-name" from config?
            #    # TODO:
            #    #

            # continuous
            #  z-score?  https://www.analyticsvidhya.com/blog/2015/11/8-ways-deal-continuous-variables-predictive-modeling/
            #  log transformation
            # https://www.freecodecamp.org/news/feature-engineering-and-feature-selection-for-beginners/
            # min-max Normalization (https://www.freecodecamp.org/news/feature-engineering-and-feature-selection-for-beginners/)
            # standardization (https://www.freecodecamp.org/news/feature-engineering-and-feature-selection-for-beginners/)

            # scaling


            # TODO: add a field level "missing" configuration to specify a strategy for handling missing sources
            # N/A, null, Empty, ?, none, empty, -, NaN, etc.
            # Strategies: variable deletion, mean/median imputation, most common value, ???
    if args.verbose:
        print("Data:", df)

# show the dictionary
if args.verbose:
    print("Columns:",args.columns)
    print("Dictionary:",dictionary)

exit(0)
# try using merge to join sources sources
print("sources.keys:", data.keys())
# summarize our sources
for d in data.keys():
    print()
    print()
    print()
    print()
    print("columns for ",d,":")
    # print(sources[d].describe())
    print(data[d].columns.values.tolist())

print()
print()
print()
exit(0)
# determine best configuration for pre-defining possible merges

print("Merging...")
merge1 = pd.merge(data['clinvar-variant-summary-summary'], data['clinvar-variant-summary-vrs'], left_on='VariationID', right_on='clinvar_variation_id')
merge2 = pd.merge(merge1, data['gencc-submissions-submissions'], left_on='GeneSymbol', right_on='gene_symbol')
merge3 = pd.merge(merge2, data['clingen-dosage-dosage'], left_on='gene_symbol', right_on='GENE SYMBOL')
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

