import pandas as pd
import argparse

# TODO:
#  * investigate python template libraries for LLM text generation
#  * determine best way to configure "joins" of source files
#  * should I eliminate leading # on column names from ClinVar file?

parser = argparse.ArgumentParser(
                    prog='clingen-ai-tools',
                    description='Prepares ClinVar, ClinGen, and GenCC data for use by ML and LLM analysis.',
                    add_help=True,
                    allow_abbrev=True,
                    exit_on_error=True)

parser.add_argument('--onehot', action='store_true', help="Generate one-hot encodings for columns that support it.")
parser.add_argument('--categories', action='store_true', help="Generate category encodings for columns that support it.")
parser.add_argument('--continuous', action='store_true', help="Generate continuous variables for columns that support it.")
parser.add_argument('-s', '--sources', help="Comma-delimited list of sources to include based on 'name' in sources.dict.",
    type=lambda s: [item for item in s.split(',')]) # validate below against configured sources
parser.add_argument('-c', '--columns', help="Comma-delimited list of columns to include based on 'column' in *.dict files.",
    type=lambda s: [item for item in s.split(',')]) # validate below against configured dictionaries

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

# read configuration dictionary
sourcefiles = pd.read_csv('sources.csv', sep=',', header=0, quotechar='"', engine='python')

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

# if verbose
# print("Using source files: ", sources)

# restrict source list configuration by names
sourcefiles = sourcefiles.loc[sourcefiles['name'].isin(sources)]
# if verbose
# print("Source configurations: ", sourcefiles)

# setup data dictionary
dictionary = pd.DataFrame(columns=['directory', 'file', 'column', 'comment', 'onehot', 'category', 'continuous', 'text'])
data = dict()

# create common dictionary (already limited by selected sources)
for index, sourcefile in sourcefiles.iterrows():
    print(sourcefile['directory'], sourcefile['file'], sourcefile['dictionary'], "sep='" + sourcefile['delimiter'] + "'")
    delimiter = sourcefile['delimiter']
    if delimiter == 'tab':
        separator = '\t'
    elif delimiter == 'comma':
        separator = ','
    else:
        separator = None

    # read source dictionary
    print("Reading dictionary")
    dic = pd.read_csv(sourcefile['directory'] + '/' + sourcefile['dictionary'])
    print(dic)
    for i, r in dic.iterrows():
        # add dictionary entry to global diction if specified on command line, or if no columns specified on command line
        if args.columns == None or r['column'] in args.columns:
            dictionary.loc[len(dictionary)] = [sourcefile['directory'], sourcefile['file'], r['column'], r['comment'], r['onehot'], r['category'], r['continuous'], r['text']]
    print("Dictionary processed")

    # read source data
    # if verbose
    print("Reading",sourcefile['name'],"...")



    #bad_lines_fp = open('bad_lines.csv', 'a')
    if args.columns == None:
        data.update({sourcefile['name']: pd.read_csv(sourcefile['directory'] + '/' + sourcefile['file'],
                                                     header=sourcefile['header_row'], sep=separator,
                                                     skiprows=sourcefile['skip_rows'], engine='python',
                                                     quoting=sourcefile['quoting'],
                                                     on_bad_lines='warn')})
    else:
        sourcecolumns = list(set(dic['column']) & set(args.columns))
        data.update({sourcefile['name']: pd.read_csv(sourcefile['directory'] + '/' + sourcefile['file'],
                                                     usecols=sourcecolumns,
                                                     header=sourcefile['header_row'], sep=separator,
                                                     skiprows=sourcefile['skip_rows'], engine='python',
                                                     quoting=sourcefile['quoting'],
                                                     on_bad_lines='warn')})
    # if verbose
    print("Finshed reading source file")
    print(sourcefile['name'],":",data[sourcefile['name']].head(), data[sourcefile['name']].info())
    #bad_lines_fp.close()


# show the dictionary
# if verbose
# print("Columns:",args.columns)
# print("Dictionary:",dictionary)

exit(0)
# try using merge to join data sources
print("data.keys:", data.keys())
# summarize our data
for d in data.keys():
    print()
    print()
    print()
    print()
    print("columns for ",d,":")
    # print(data[d].describe())
    print(data[d].columns.values.tolist())

print()
print()
print()
exit(0)
# determine best configuration for pre-defining possible merges

print("Merging...")
merge1 = pd.merge(data['clinvar-summary'], data['clinvar-vrs'], left_on='VariationID', right_on='clinvar_variation_id')
merge2 = pd.merge(merge1, data['gencc-submissions'], left_on='GeneSymbol', right_on='gene_symbol')
merge3 = pd.merge(merge2, data['clingen-dosage'], left_on='gene_symbol', right_on='GENE SYMBOL')
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

