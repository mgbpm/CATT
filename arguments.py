import argparse

#########################
#
# PROGRAM ARGUMENTS
#
#########################


def parse():
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
                        help="Duplicate rows when configured columns have lists of values (i.e. list of genes).")
    parser.add_argument('--map', action='store_true',
                        help="Generate new columns based on mapping group configuration.")
    parser.add_argument('--na-value', action='store', dest='na_value', type=int, default=None,
                        help='A numeric value to use when a value is n/a. Defaults=None. Also configurable per column.')
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
                        help='Filter to a specific variant (CV VariationID). Variable must be tagged in join-group.')
    parser.add_argument('--gene',  action='store', type=str,
                        help='Filter to a specific gene (symbol). Variable must be tagged in join-group.')

    return parser.parse_args()
