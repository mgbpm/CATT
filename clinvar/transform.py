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

print("Transforming variant_summary.txt for AI/ML")

df = pd.read_csv('variant_summary.txt', sep='\t', header=0, low_memory=False)

# Field                     Category    One-hot
# AlleleID                      N           N
# Type                          Y           N
# Name                          N           N
# GeneID                        Y           N
# GeneSymbol                    Y           Y
# HGNC_ID                       N           N
# ClinicalSignificance          Y           Y
# ClinSigSimple                 Y           Y
# LastEvaluated                 N           N
# RS# (dbSNP)                   ?           ?  let's see how many unique values
# nsv/esv (dbVar)               ?           ?  let's see how many unique values
# RCVaccession                  N           N
# PhenotypeIDS                  N           N
# PhenotypeList                 Y           Y
# Origin                        Y           Y
# OriginSimple                  Y           Y
# Assembly                      Y           Y
# ChromosomeAccession           Y           Y
# Chromosome                    Y           Y
# Start                         N           N
# Stop                          N           N
# ReferenceAllele               Y           Y
# AlternateAllele               Y           Y
# Cytogenetic                   Y           Y
# ReviewStatus                  Y           Y
# NumberSubmitters              Y           Y
# Guidelines                    Y           Y
# TestedInGTR                   Y           Y
# OtherIDs                      Y           Y
# SubmitterCategories           Y           Y
# VariationID                   Y           Y
# PositionVCF                   Y           Y
# ReferenceAlleleVCF            Y           Y
# AlternateAlleleVCF            Y           Y


# one_hot_class = pd.get_dummies(df['classification_title'])
# df = df.join(one_hot_class)
# one_hot_moi = pd.get_dummies(df['moi_title'])
# df = df.join(one_hot_moi)
# one_hot_gene = pd.get_dummies(df['gene_symbol'])
# df = df.join(one_hot_gene)
# one_hot_gene = pd.get_dummies(df['disease_title'])
# df = df.join(one_hot_gene)
# one_hot_gene = pd.get_dummies(df['submitter_title'])
# df = df.join(one_hot_gene)

print("Type: ",df.Type.unique())
print("ClinicalSignificance: ",df.ClinicalSignificance.unique())
print("ClinSigSimple: ",df.ClinSigSimple.unique())
print("Origin: ",df.Origin.unique())
print("OriginSimple: ",df.OriginSimple.unique())
print("Assembly: ",df.Assembly.unique())
print("ChromosomeAccession: ",df.ChromosomeAccession.unique())
print("Chromosome: ",df.Chromosome.unique())
print("ReferenceAllele: ",df.ReferenceAllele.unique())
print("AlternateAllele: ",df.AlternateAllele.unique())
print("Cytogenetic: ",df.Cytogenetic.unique())
print("ReviewStatus: ",df.ReviewStatus.unique())
print("Guidelines: ",df.Guidelines.unique())
print("TestedInGTR: ",df.TestedInGTR.unique())


# with pd.option_context('display.max_columns', 100):
#    print(df.describe(include='all'))

# write to output file
# df.to_csv(outputFile, sep="\t")