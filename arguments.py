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

    # configuration management
    parser.add_argument('--force', action='store_true',
                        help="Download datafiles even if present and overwrite.")
    parser.add_argument('--counts', action='store_true',
                        help="Print unique value counts for columns (helpful for deciding on mappings and categories).")

    # output control
    parser.add_argument('--sources',
                        help="Comma-delimited list of sources to include based on name in each config.yml.",
                        type=lambda s: [str(item) for item in s.split(',')])  # validate against configured sources
    parser.add_argument('--columns',
                        help="Comma-delimited list of columns to include based on 'column' in *.dict files.",
                        type=lambda s: [str(item) for item in s.split(',')])  # validate against configured dictionaries
    parser.add_argument('--joined-output',  action='store', dest='output', type=str, default=None,
                        help='The desired output file name.')
    parser.add_argument('--variant',  action='store', type=str,
                        help='Filter to a specific variant (CV VariationID). Variable must be tagged in join-group.')
    parser.add_argument('--gene',  action='store', type=str,
                        help='Filter to a specific gene (symbol). Variable must be tagged in join-group.')
    parser.add_argument('--template-output', action='store', dest='text_output', type=str, default=None,
                        help="Generate text output file using template values to specified file.")

    args = parser.parse_args()

    # if --join-output then set flag for joining
    if args.output is not None:
        args.join = True
    else:
        args.join = False

    # if --template-output is set, then assume we want --template also
    if args.text_output is not None and not args.template:
        args.template = True

    # if joining, then need a list of sources in desired join order
    if args.join and not args.sources:
        print("ERROR: must specify --sources with --joined-output. The sources list is the list of data files to join.")
        exit(-1)


    return args
