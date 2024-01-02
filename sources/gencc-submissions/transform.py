import pandas as pd
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-O", "--outputfile", type=str)
parser.add_argument("-g", "--gene", type=str)

#parser.add_argument("-s", "--sample", type=int)

args = parser.parse_args()
outputFile = args.outputfile
geneFilter = args.gene

print("Generate file:",outputFile)

print("Transforming gencc-submissions-submissions.tsv for AI/ML")

df = pd.read_csv('gencc-submissions.tsv', sep='\t', header=0)

# Field                     Category    One-hot   Continuous
# uuid                          N           N
# gene_curie                    Y           N
# gene_symbol                   Y           Y
# disease_curie                 Y           N
# disease_title                 Y           Y
# disease_original_curie        Y           N
# disease_original_title        Y           N
# classification_curie          Y           N
# classification_title          Y           Y
# moi_curie                     Y           N
# moi_title                     Y           Y
# submitter_curie               Y           N
# submitter_title               Y           Y
# submitted_as_hgnc_id
# submitted_as_hgnc_symbol
# submitted_as_disease_id
# submitted_as_disease_name
# submitted_as_moi_id
# submitted_as_moi_name
# submitted_as_submitter_id
# submitted_as_submitter_name
# submitted_as_classification_id
# submitted_as_classification_name
# submitted_as_date
# submitted_as_public_report_url
# submitted_as_notes
# submitted_as_pmids
# submitted_as_assertion_criteria_url
# submitted_as_submission_id
# submitted_run_date

one_hot_class = pd.get_dummies(df['classification_title'])
df = df.join(one_hot_class)
one_hot_moi = pd.get_dummies(df['moi_title'])
df = df.join(one_hot_moi)
one_hot_gene = pd.get_dummies(df['gene_symbol'])
df = df.join(one_hot_gene)
one_hot_gene = pd.get_dummies(df['disease_title'])
df = df.join(one_hot_gene)
one_hot_gene = pd.get_dummies(df['submitter_title'])
df = df.join(one_hot_gene)


with pd.option_context('display.max_columns', 100):
    print(df.describe(include='all'))

# write to output file
df.to_csv(outputFile, sep="\t")