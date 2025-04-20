<img src="https://github.com/mgbpm/CATT/blob/master/icon_github.jpg" width="1024" align="center"/> 

---
Tool for preparing ClinGen, ClinVar and GenCC public datasets for use in machine learning and large language model
analysis. The tool is command line-based but familiarity with Python is helpful.

* Provides pre-configured numerical mapping of significant categorical data elements.
* Allows simplified joining across large data sets on common values into a consolidated CSV.
* Generates per source record text summary for use by LLMs, and combines across sources into single output.

## Acknowledgements

This software was funded by NHGRI and ClinGen.

## Features
* Pre-configured for multiple data source files from ClinGen, ClinVar and GenCC.
* Automatic download of source files when files are available on public servers.
* Filtering output by gene or variant id.
* Filtering output to include specified columns.
* Output encoding for one-hot, categorical, and mapping values to ranks or new values
* Date handling
* Included numerical and other mappings for subset of columns
* Expands value-list columns to multiple rows (e.g. gene value of "MYH7,BRCA1" becomes two rows)
* Extendable to new data sources through configuration
* Generates new configuration files for new sources, including value counts
* Generates LLM suitable text file based on templated per source per row input

## Prerequisites / Getting Started

Python 3 is required (tested with Python 3.9.18), as well as the following modules, which you may optionally 
configure in a virtual environment.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```
or
```sh
 python -m pip install pandas argparse sklearn.preprocessing pyyaml requests dateparser genshi
```

Please use Pandas 2.0.0 or greater.

## Usage

To use CATT, run the `main.py` script in the root project directory. 

Command line options include:

| Option                         | Description                                                                                                   |
|--------------------------------|---------------------------------------------------------------------------------------------------------------|
| <nobr>--loglevel</nobr>        | Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).                                                    |
| <nobr>--template</nobr>        | Generate new output column, one per row, based on template value in config.yml.                               |
| <nobr>--template-output</nobr> | Generate a composite text file from all template values as specified file. Requires --template.               |
| <nobr>--days</nobr>            | Generate new days_... column for dates as days since 1/1/1970.                                                |
| <nobr>--age</nobr>             | Generate new age_... column for dates as days since today.                                                    |
| <nobr>--onehot</nobr>          | Generate output for columns configured to support one-hot encoding.                                           |
| <nobr>--categories</nobr>      | Generate output for columns configured to support categorical encoding.                                       |
| <nobr>--expand</nobr>          | For columns configured to expand, generate a row for each value if more than one value for a row.             | 
| <nobr>--map</nobr>             | For values configured to map, generate new columns with values mapped based on the configuration mapping.csv. |
| <nobr>--na-value</nobr>        | Set global replacement for NaN / missing values and trigger replacement including field level replacement.    |
| <nobr>--force</nobr>           | Download source files even if already present.                                                                |
| <nobr>--counts</nobr>          | Print value counts for the source files (helpful for determining mapping candidates).                         |
| <nobr>--sources</nobr>         | List of sources to process, default is all sources.                                                           |
| <nobr>--columns</nobr>         | Column names to output. May specify comma separated list. Default is all columns.                             |
| <nobr>--joined-output</nobr>   | Generate a joined output file using left joins following the --sources list. --sources must be specified.     |
| <nobr>--variant</nobr>         | Filter output by clinvar variation-id(s). May specify comma separated list. Default include all records.      | 
| <nobr>--gene</nobr>            | Filter output by gene symbol(s). May specify comma separated list. Default is all records.                    |

## Example Usage

Force downloads of all sources, even if files already exist locally.
```sh
python main.py --force --loglevel=info
```

Generate mappings, categorical and onehot encodings, filter by gene MYH7 and left join the sources vrs, 
clinvar-variant-summary, gencc-submissions, and clingen-overall-scores-adult.
```sh
python main.py --loglevel=info --map --categories --expand --onehot --gene="MYH7" --joined-output="output.csv" --sources="vrs,clinvar-variant-summary,gencc-submissions,clingen-overall-scores-adult"
```

Generate individual output files for vrs and clingen-overall-scores-pediatric, while expanding references to multiple genes,
and producing onehot and categorical encodings.
```sh
python main.py --loglevel=debug --expand --onehot --categories --sources="clingen-overall-scores-pediatric,vrs"
```

Generate both individual and a joined output file from multiple sources or VariationID 8602 and include generated text template for each row and source.
```sh
python main.py --loglevel=info --template --sources="clinvar-submission-summary,clinvar-variant-summary,gencc-submissions,clingen-dosage,clingen-gene-disease,vrs" --joined-output="output.csv" --variant=8602
```

Generate text-only file from generated template fields in filtered records. Suitable for use with LLMs.
```sh
python main.py --loglevel=info --expand --sources="clinvar-submission-summary,clinvar-variant-summary,vrs,gencc-submissions,clingen-gene-disease,clingen-consensus-assertions-adult,clingen-consensus-assertions-pediatric,clingen-dosage,clingen-overall-scores-adult,clingen-overall-scores-pediatric" --template --template-output="variant_5760_gene_KISS1R.txt" --variant=5760 --gene=KISS1R
```

Generate text-only and csv-only files from generated template fields in filtered records. Suitable for use with LLMs. (Batch Processing Version)
```sh
bash batch_txt_results.sh {your input file} {your output folder}
bash batch_csv_results.sh {your input file} {your output folder}
```
Note that every row in the {your input file} represents a variant ID, an example file is the `example_input_file_for_llm_summary.txt`, and the default output folder is `results/`. An example execution is `bash batch_txt_results example_input_file_for_llm_summary.txt results/`


## Source Configuration
The program looks for data sources in the ./sources subdirectory. By convention, the "name" of a source is the name of
its subdirectory. Each source subdirectory has from 2 to 3 configuration files: `config.yml`, `dictionary.csv`, and 
optionally `mapping.csv`. These contain metadata for the file, fields, and field values of the source, and control
how the source is downloaded and transformed by the program.

### config.yml
A valid source is one that has a `config.yml` file in its directory.
A `config.yml` file contains meta-data about the source such as the url for downloading, optional md5 checksum
file, file format (csv or tab-delimited), quoting strategy, header row location, whether to unzip the downloaded file,
and whether to strip extraneous # characters from the header.

This example shows the `config.yml` for the ClinVar Variant Summary source. The `name` matches the source subdirectory
name. The `url` is used to download the data file to the `download_file` (if specified) or `file` (if download_file is 
not specified). The downloaded file is then uncompressed as directed by the `gzip` flag to `file`.

The file header is the first (0) row following the list of rows to skip `skip_rows`. The format of the file is
tab-delimited (`tab`).

The `template` value is used with the --template command line option to generate a textual description of 
each row in the file. The template uses Genshi's NewTextTemplate module (see 
https://shorturl.at/VavlZ). Each column value is available to the template as
dict.column_name, or if the column name has spaces use dict['column name'].

```yaml
--- # ClinVar Submission Summary
- name: clinvar-submission-summary
  url: https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/submission_summary.txt.gz
  download_file: submission_summary.txt.gz
  gzip: 1
  file: submission_summary.txt
  header_row: 0
  skip_rows: 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16
  delimiter: tab
  quoting: 3
  strip_hash: 1
  md5_url: https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/submission_summary.txt.gz.md5
  md5_file: submission_summary.txt.gz.md5
  template: >
    ${dict.Submitter} has classified the variant with ClinVar Variation ID ${dict.VariationID} in the 
    {% choose %}{% when len(str(dict.SubmittedGeneSymbol)) > 0 %}${dict.SubmittedGeneSymbol}{% end %}
    {% otherwise %}not provided{% end %}{% end %} gene as ${dict.ClinicalSignificance}. The accession number or 
    SCV ID for this submission 
    is ${dict.SCV}. This variant has been associated with the following condition(s) by the submitter: 
    ${dict.ReportedPhenotypeInfo}. This variant was last evaluated by the submitter on 
    {% choose %}{% when len(str(dict.DateLastEvaluated)) > 0 %}${dict.DateLastEvaluated}{% end %}
    {% otherwise %}"date not provided"{% end %}{% end %}, and the 
    review status of this submission is: ${dict.ReviewStatus}. The setting in which the variant classification was made 
    is: ${dict.CollectionMethod}. The submitter has provided the following evidence to support their variant 
    classification: 
    {% choose %}{% when len(str(dict.Description)) > 0 %}“${dict.Description}”{% end %}
    {% otherwise %}"no details provided"{% end %}{% end %}
```

| Setting       | Description                                                                                                                                |
|---------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| name          | Unique name for the source that should match the subdirectory name.                                                                        |
| url           | A web url suitable for downloading the data file.                                                                                          |
| download_file | Optional. When downloading a compressed file, download_file is the name of the compressed file.                                            |
| gzip          | 0 or 1, to indicate whether to decompress the downloaded file.                                                                             |
| file          | The name of the downloaded file (if uncompressed) or the name of the file after decompressing.                                             |
| header_row    | The row number, staring at 0 for the first row, containing the column headers. Count beings following any skipped rows.                    |
| skip_rows     | A comma separated list of rows to skip (0 first row). Useful for when there are extra header rows with meta data in the source file.       |
| delimiter     | `tab` or `comma`, to inform about file structure (csv or tsv).                                                                             |
| quoting       | Default 0. Pandas quoting strategy to use when reading the file: {0 = QUOTE_MINIMAL, 1 = QUOTE_ALL, 2 = QUOTE_NONNUMERIC, 3 = QUOTE_NONE}. |
| strip_hash    | 0 or 1, to indicate whether to strip leading and trailing hash (#) characters from column headers.                                         |
| md5_url       | Optional. A web url suitable for downloading an md5 checksum file.                                                                         |
| md5_file      | Optional. The name of the downloaded md5 checksum file.                                                                                    |
| template      | Optional. A text template in Genshi format for use with --template in which text is processed per row and added as column                  |

### dictionary.csv
Each source should also have a `dictionary.csv` file which provides meta-data about the columns in the source file.
It includes a row for each column which contains the field name, definition, join-ability group, and flags to enable
one-hot encoding, categorical encoding, mapping, row expansion, etc.

The below shows a sample dictionary for the clingen-dosage source. "GENE SYMBOL" and "HGNC ID" are configured to
support the join-group's "gene-symbol" and "hgnc-id", allowing those columns to be used to join with other source files
containing either of those join-groups. The "HAPLOINSUFFICIENCY" and "TRIPLOSENSITIVITY" are configured for both
categorical encoding (string values to numbers) and to mapping encoding which will utilize the mapping.csv to generate
additional columns for the output based on each value.

```csv
"column","comment",join-group,onehot,category,continuous,format,map,days,age,expand,na-value
GENE SYMBOL,"Official gene symbol of the assertion.",gene-symbol,FALSE,FALSE,FALSE,,FALSE,FALSE,FALSE,FALSE,""
"HGNC ID","HGNC id for the specified gene in the form `HGNC:<hgnc gene id>`",hgnc-id,FALSE,FALSE,FALSE,,FALSE,FALSE,FALSE,FALSE,""
"HAPLOINSUFFICIENCY","Interpretation category for haploinsufficiency and inheritance mode if applicable, for example 'Gene Associated with Autosomal Recessive Phenotype' or 'Little Evidence for Haploinsufficiency'.",,FALSE,TRUE,FALSE,,TRUE,FALSE,FALSE,FALSE,""
"TRIPLOSENSITIVITY","Interpretation category for triploinsufficiency and inheritance mode if applicable, for example 'Sufficient Evidence for Triplosensitivity', 'Dosage Sensitivity Unlikely' or 'Little Evidence for Triploinsufficiency'.",,FALSE,TRUE,FALSE,,TRUE,FALSE,FALSE,FALSE,""
"ONLINE REPORT","A URL to the dosage sensitivity report at clinicalgenome.org.",,FALSE,FALSE,FALSE,,FALSE,FALSE,FALSE,FALSE,""
"DATE","Date added or last updated.",,FALSE,FALSE,FALSE,"%Y-%m-%dT%H:%M:%SZ",FALSE,TRUE,TRUE,FALSE,""
```

The `dictionary.csv` contains the following columns:

| Column     | Description                                                                                                                                                                                        |
|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| column     | The exact column header name from the file, stripped of hashes if configured to do so.                                                                                                             |
| comment    | A brief description of the column.                                                                                                                                                                 |
| join-group | A token alias string used to designate columns across different sources that contain the same information values, such as a gene symbol. Required for supporting joining across files with --join. |
| onehot     | With --onehot, generate new output columns for each value of the column, with values of 0 or 1 depending on if the row has the specific value.                                                     |
| category   | With --categories, generate a new column with values mapped to unique numbers.                                                                                                                     |
| continuous | Placeholder for future feature. Currently not implemented or supported.                                                                                                                            |
| format     | For date columns using days/age flag, this is the date format of the field (see common formats below).                                                                                             |
| map        | With --map, use `mapping.csv` to create new output columns based on values in the column.                                                                                                          |
| days       | Not yet implemented. With --days, generate a new output column with the number of days since Jan 1 1970 to the date value.                                                                         |
| age        | Not yet implemented. With --age, generate a new output column with the number of days between today and the date value.                                                                            |
| expand     | With --expand, if a column has a list of values (comma-separated) in a row, generate one additional output row per value with a single value for each item. The original row is left intact.       |
| na-value   | A field level replacement for NaN / missing values, which are replace when using --na-value                                                                                                        |

Common date formats in source files for use in the `format` column include the following. If a date does not match the
pattern, the program will attempt to determine using a fallback approach.

| Date/time Value                 | Format                   |
|---------------------------------|--------------------------|
| Mon Nov 02 21:15:11 UTC 2020    | %a %b %d %H:%M%S %Z %Y   |
| 2016-06-08T14:14:30Z            | %Y-%m-%dT%H:%M:%SZ       |
| 2018-06-07T16:00:00.000Z        | %Y-%m-%dT%H:%M:%S.%fZ    |
| Wed, 01 Feb 2023 00:00:00 -0000 | %a, %d %b %Y %H:%M:%S %z |
| Mar 23, 2023                    | %b %d, %Y                |
| 2020-12-24                      | %Y-%m-%d                 |
| 2020-06-18 13:31:17             | %Y-%m-%d %H:%M:%S        |

### mapping.csv
Each source may optionally have a `mapping.csv` file. If the `map` column is set to true in the dictionary for a 
specific field, then the mapping file will be used to map values in the specified column to new values as specified in
the map file. Multiple mapping sets can exist for a field and each will generate a new output column in which values 
for the original field are mapped to new values via a simple lookup strategy. The new output column will be named 
according to the `map-name` column in the map.

The `mapping.csv` file for the `clingen-dosage` source is as follows. The `column` matches the dictionary and header
column name, the `value` contains the specific values that the column may contain, the `map-name` is the name of the
new output column to create for the mapping, and `map-value` is the new value to set in the new output column based
on the original column value.

```csv
column,value,frequency,map-name,map-value
HAPLOINSUFFICIENCY,Gene Associated with Autosomal Recessive Phenotype,736,haplo-insuff-rank,-0.01
HAPLOINSUFFICIENCY,Sufficient Evidence for Haploinsufficiency,365,haplo-insuff-rank,0.99
HAPLOINSUFFICIENCY,No Evidence for Haploinsufficiency,262,haplo-insuff-rank,0.5
HAPLOINSUFFICIENCY,Little Evidence for Haploinsufficiency,117,haplo-insuff-rank,0.75
HAPLOINSUFFICIENCY,Dosage Sensitivity Unlikely,35,haplo-insuff-rank,0.01
HAPLOINSUFFICIENCY,Emerging Evidence for Haploinsufficiency,26,haplo-insuff-rank,0.9
TRIPLOSENSITIVITY,No Evidence for Triplosensitivity,1248,triplo-insuff-rank,0.5
TRIPLOSENSITIVITY,Little Evidence for Triplosensitivity,11,triplo-insuff-rank,0.75
TRIPLOSENSITIVITY,Emerging Evidence for Triplosensitivity,3,triplo-insuff-rank,0.9
TRIPLOSENSITIVITY,Dosage Sensitivity Unlikely,3,triplo-insuff-rank,0.01
TRIPLOSENSITIVITY,Sufficient Evidence for Triplosensitivity,2,triplo-insuff-rank,0.99
TRIPLOSENSITIVITY,Gene Associated with Autosomal Recessive Phenotype,1,triplo-insuff-rank,-0.01
```

A `mapping.csv` file contains the following columns:

| Column    | Description                                                                                                              |
|-----------|--------------------------------------------------------------------------------------------------------------------------|
| column    | The name of the column in the source file, which matches the header name and the dictionary entry.                       |
| value     | The distinct values of the original column in the source file (will be mapped to a new value).                           |
| frequency | Optional. Created during configuration auto-generation to give context to the frequency of the value in the source file. |
| map-name  | The name of the new column to be created for the mapping in the output file.                                             |
| map-value | The new value to be mapped to based on the existing column value.                                                        |

## Adding a New Source

To add a new source data file, first create a new subdirectory in the ./sources directory. Ideally no spaces in the 
directory name. Then run the program using --sources="<subdirectory nanme>". First time it will create
a template `config.yml`. Edit the `config.yml` and specify the url, file name, etc. Run again, and it will
download the file and generate a `dictionary.csv` template. Edit the dictionary to configure. If any fields
will use mapping, then set the map flag in the dictionary and re-run. It will generate a template mapping.csv.

```sh
cd ./sources
mkdir new-source-file-name # <== use your desired source name here
cd ..
python main.py --sources="new-source-file-name" # <== use your source name here
```
This will create a `config.yml` in the ./new-source-file-name directory which will need to be edited.

```yaml
--- # Source file description
- name: source-name # usually directory name
  suffix: abc # a suffix appended to column names when joining and duplicates are encountered
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
```

Now set each of the values in the new `config.yml` to meet the requirements. Usually, you will need a `name`,
`url`, `file`, and `delimiter` choice at a minimum.

Once you've made the edits, run the program again still specifying the --sources option.

```sh
python main.py --sources="new-source-file-name"
```

If the file has been successfully downloaded, it will generate a template for `dictionary.csv`.

```sh
python main.py --sources="new-source-file-name"
```

Edit the new `dictionary.csv` and set the flags and configurations for each column. Most flags default to False.
If you configure any columns for mapping, then if you run again it will generate a mapping file
template for those columns with the known values in the data file with the frequency data of each value.

```sh
python main.py --sources="new-source-file-name"
```

Edit the `mapping.csv` file to create the specific output values and mapping sets you desire.
