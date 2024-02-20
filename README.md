# clingen-ai-tools
Tools for preparing ClinGen, ClinVar and GenCC datasets for use in machine learning and Large Language Model analysis.

## Features
* Pre-configured for multiple data source files from ClinGen, ClinVar and GenCC.
* Automatic download of source files when files are available on public servers.
* Filtering output by gene or variant id.
* Filtering output to include specified columns.
* Output encoding for one-hot, categorical, and mapping values to ranks or new values
* Future: date handling
* Included mappings for subset of columns
* Expands value-list columns to multiple rows
* Extendable to new data sources through configuration
* Generates new configuration files for new sources, including value counts

## Usage

To use the clingen-ai-tools, run the `main.py` script in the ./tools sub-directory. 

Command line options include:

| Option            | Description                                                                                                            |
|-------------------|------------------------------------------------------------------------------------------------------------------------|
| --debug           | Provide detailed debugging information.                                                                                |
| --info            | Provide high level progress information.                                                                               |
| --onehot          | Generate output for columns configured to support one-hot encoding.                                                    |
| --categories      | Generate output for columns configured to support categorical encoding.                                                |
| --expand          | For columns configured to expand, generate a row for each value if more than one value for a row.                      | 
| --map             | For values configured to map, generate new columns with values mapped based on the configuration mapping.csv.          |
| --download        | Download source files when not present. Download source files when not present. Configured with config.yml.            |
| --force           | Download source files even if already present.                                                                         |
| --counts          | Generate value counts for the source files (helpful for determining mapping candidates).                               |
| --generate-config | Generate configuration files (config.yml, dictionary.csv, mapping.csv). May take multiple steps if no files yet exist. |
| --sources         | List of sources to process, default is all sources.                                                                    |
| --columns         | Column names to output. May specify comma separated list. Default is all columns.                                      |
| --output          | Name of the overall output file. Default is `output.csv`.                                                              |
| --individual      | Generate individual output files, one per source, that include the encodings and mappings.                             |
| --join            | Create a joined data file using left joins following the --sources list. --sources must be specified.                  |
| --variant         | Filter output by clinvar variation-id(s). May specify comma separated list. Default include all records.               | 
| --gene            | Filter output by gene symbol(s). May specify comma separated list. Default is all records.                             |

## Example Usage

Force downloads of all sources.
```
python main.py --download --force --info
```
Generate mappings, categorical and onehot encodings, filter by gene MYH7 and left join the sources vrs, 
clinvar-variant-summary, gencc-submissions, and clingen-overall-scores-adult.
``` 
python main.py --info --map --categories --expand --onehot --gene="MYH7" --join --sources="vrs,clinvar-variant-summary,gencc-submissions,clingen-overall-scores-adult"
```

Generate an individual output file for vrs and clingen-overal-scores-pediatric, while expanding references to multiple genes,
and producing onehot and categorical encodings.
```
python main.py --debug --expand --onehot -cateogries --individual --sources="clingen-overall-scores-pediatric,vrs"
```

## Source Configuration

The program looks for sources in the ./sources sub-directory. A valid source is one that has a `config.yml` file.
A `config.yml` file contains meta-data about the source such as the url for downloading, optional md5 checksum
file, file format (csv or tab-delimited), quoting strategy, header row location, etc.

Each source should also have a `dictionary.csv` file which provides meta-data about the columns in the source file.
It includes a row for each column which contains the field name, definition, joinability group, and flags to enable
one-hot encoding, categorical encoding, mapping, row expansion, etc.

Each source may optionally have `mapping.csv` file. If the `map` column is set to true in the dictionary for a specific
field, then the mapping file will be used to map values in the specified column to new values as specified in the map
file. Multiple mapping sets can exist for a field and each will generate a new output column in which values for the
original field are mapped to new values via a simple lookup strategy. The new output column will be named according
to the `map-name` column in the map.
