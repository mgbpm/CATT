### The file `variant-summary.txt` can be downloaded from the NCBI FTP website at `https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz`. The file contains the following columns:

### The ClinVar data dictionary is available at https://www.ncbi.nlm.nih.gov/projects/clinvar/ClinVarDataDictionary.pdf.

### Columns include
#AlleleID	Type	Name	GeneID	GeneSymbol	HGNC_ID	ClinicalSignificance	ClinSigSimple	LastEvaluated	RS# (dbSNP)	nsv/esv (dbVar)	RCVaccession	PhenotypeIDS	PhenotypeList	Origin	OriginSimple	Assembly	ChromosomeAccession	Chromosome	Start	Stop	ReferenceAllele	AlternateAllele	Cytogenetic	ReviewStatus	NumberSubmitters	Guidelines	TestedInGTR	OtherIDs	SubmitterCategories	VariationID	PositionVCF	ReferenceAlleleVCF	AlternateAlleleVCF
#15041	Indel	NM_014855.3(AP5Z1):c.80_83delinsTGCTGTAAACTGTAACTGTAAA (p.Arg27_Ile28delinsLeuLeuTer)	9907	AP5Z1	HGNC:22197	Pathogenic	1	-	397704705	-	RCV000000012	MONDO:MONDO:0013342,MedGen:C3150901,OMIM:613647,Orphanet:306511	Hereditary spastic paraplegia 48	germline;unknown	germline	GRCh37	NC_000007.13	7	4820844	4820847	na	na	7p22.1	criteria provided, single submitter	2	-	N	ClinGen:CA215070,OMIM:613653.0001	3	2	4820844	GGAT	TGCTGTAAACTGTAACTGTAAA

"AlleleID"
: A unique integer identifier, the Allele ID, is assigned to each individual variant in ClinVar. 
: The numbering systems for the Allele ID and the Variation ID described above overlap, so it is important to note the 
: context of any integer identifier.

"Type"
: The type of mutation.
: ['Indel' 'Deletion' 'single nucleotide variant' 'Duplication'
: 'Microsatellite' 'Insertion' 'Variation' 'Complex' 'Translocation'
: 'protein only' 'Inversion' 'copy number gain' 'fusion' 'copy number loss'
: 'Tandem duplication']

"Name"
: Name of variant using standard nomenclatures (transcript, gene, cDNA change, protein change)
: Example: NM_014855.3(AP5Z1):c.80_83delinsTGCTGTAAACTGTAACTGTAAA (p.Arg27_Ile28delinsLeuLeuTer)

"GeneID"
: The Entrez ID for the gene.
: Example: '9907'

"GeneSymbol"
: TODO: verify this is accurate
: The official HGNC gene symbol of the gene associated with the variant.
: Example: 'AP5Z1'

"HGNC_ID"
: Then HGNC ID of the gene associated with the variant.
: Example 'HGNC:22197'

"ClinicalSignificance"
: The clinical significance of the variant as text value including modifiers.
: ['Pathogenic' 'Uncertain significance'
:  'Conflicting interpretations of pathogenicity'
:  'Conflicting interpretations of pathogenicity; other; risk factor'
:  'Conflicting interpretations of pathogenicity; other' 'Benign'
:  'Pathogenic/Likely pathogenic' 'Likely pathogenic' 'risk factor'
:  'Likely benign' 'association' 'Likely pathogenic; risk factor'
:  'Benign/Likely benign' 'no interpretation for the single variant'
:  'Conflicting interpretations of pathogenicity; risk factor'
:  'drug response' 'Affects'
:  'Conflicting interpretations of pathogenicity; association; risk factor'
:  'Pathogenic; risk factor' 'Uncertain significance; risk factor'
:  'Benign/Likely benign; other' 'Pathogenic/Likely pathogenic; risk factor'
:  'Benign; risk factor' 'Benign; other' 'protective; risk factor'
:  'Likely benign; other'
:  'Conflicting interpretations of pathogenicity; association'
:  'not provided' 'Pathogenic; Affects' 'Benign/Likely benign; association'
:  'association; drug response; risk factor' 'Affects; risk factor'
:  'Benign/Likely benign; other; risk factor' 'protective'
:  'Conflicting interpretations of pathogenicity; protective'
:  'drug response; risk factor' 'Pathogenic; drug response'
:  'Pathogenic; association' 'Likely risk allele'
:  'Uncertain significance/Uncertain risk allele'
:  'Uncertain risk allele; protective' 'drug response; other'
:  'Likely benign; drug response; other' 'Benign/Likely benign; risk factor'
:  'Uncertain significance; drug response'
:  'Likely pathogenic; drug response' 'other' 'Pathogenic; other'
:  'Conflicting interpretations of pathogenicity; drug response; other'
:  'Conflicting interpretations of pathogenicity; drug response'
:  'Likely pathogenic; other' 'Benign; association'
:  'Likely pathogenic; association' 'Benign; confers sensitivity'
:  'Pathogenic/Likely risk allele'
:  'Likely pathogenic/Pathogenic, low penetrance'
:  'Pathogenic/Likely pathogenic/Pathogenic, low penetrance'
:  'Pathogenic; protective' 'Pathogenic; drug response; other'
:  'other; risk factor' 'Pathogenic/Likely risk allele; risk factor'
:  'Pathogenic/Likely pathogenic; other'
:  'Pathogenic/Likely pathogenic; drug response'
:  'Conflicting interpretations of pathogenicity; association; other'
:  'association; drug response'
:  'Conflicting interpretations of pathogenicity; Affects'
:  'Pathogenic; association; protective' 'Affects; association'
:  'Pathogenic/Likely pathogenic/Pathogenic, low penetrance; other'
:  'conflicting data from submitters'
:  'Uncertain significance; Pathogenic/Likely pathogenic'
:  'Likely pathogenic/Likely risk allele'
:  'Uncertain risk allele; risk factor' 'Uncertain significance; other'
:  'Benign; drug response' 'Uncertain significance; association'
:  'Benign/Likely benign; drug response'
:  'Benign/Likely benign; drug response; other' 'association; risk factor'
:  'Uncertain risk allele' 'Pathogenic; confers sensitivity'
:  'Likely pathogenic; Affects' 'association not found'
:  'Likely benign; risk factor' 'Likely benign; association'
:  'Pathogenic/Likely pathogenic/Likely risk allele'
:  'Affects; association; other' 'confers sensitivity'
:  'confers sensitivity; other' 'Benign; Affects'
:  'Likely pathogenic, low penetrance' 'Pathogenic, low penetrance']

"ClinSigSimple"
: Simple value for clinical significance [ 1  0 -1]
: [TODO: Need to validate interpretation of values]
: 1 Pathogenic
: 0 Benign or Uncertain
: -1 No interpretation

"LastEvaluated"
: The date the variant was last evaluated by the submitter.

"RS# (dbSNP)"
: rs# in dbSNP, reported as -1 if missing

"nsv/esv (dbVar)"
:

"RCVaccession"
:

"PhenotypeIDS"
:

"PhenotypeList"
:

"Origin"
: The origin of variant and sample, such as germine vs. somatic, de novo vs. inherited (biparental, maternal, paternal)
: Exmpample: 'germline;maternal'

"OriginSimple"
: Simplified origin of variant.
: ['germline' 'not applicable' 'germline/somatic' 'somatic' 'unknown'
:  'not provided' 'tested-inconclusive']

"Assembly"
: The reference squence standard of the variant.
: ['GRCh37' 'GRCh38' 'na' 'NCBI36']

"ChromosomeAccession"
: The chromosome reference build.
: ['NC_000007.13' 'NC_000007.14' 'NC_000015.9' 'NC_000015.10' 'NC_000011.9'
:  'NC_000011.10' 'NC_000014.8' 'NC_000014.9' 'NC_000006.11' 'NC_000006.12'
:  'NC_000002.11' 'NC_000002.12' 'NC_000020.10' 'NC_000020.11'
:  'NC_000010.10' 'NC_000010.11' 'NC_000019.9' 'NC_000019.10' 'NC_000016.9'
:  'NC_000016.10' 'NC_000022.10' 'NC_000022.11' 'NC_000012.11'
:  'NC_000012.12' 'NC_000001.10' 'NC_000001.11' 'na' 'NC_000008.10'
:  'NC_000008.11' 'NC_000009.11' 'NC_000009.12' 'NC_000013.10'
:  'NC_000013.11' 'NC_000021.8' 'NC_000021.9' 'NC_000005.9' 'NC_000005.10'
:  'NC_000004.11' 'NC_000004.12' 'NC_000017.11' 'NW_003315950.2'
:  'NC_000018.9' 'NC_000018.10' 'NC_000003.11' 'NC_000003.12' 'NC_000017.10'
:  'NC_012920.1' 'NC_000024.9' 'NC_000024.10' 'NC_000023.10' 'NC_000023.11'
:  'NW_003315925.1' 'NW_009646201.1' 'NC_000003.10' 'NC_000021.7'
:  'NC_000023.9' 'NT_187614.1' 'NW_003871068.1' 'NC_000001.9' 'NC_000002.10'
:  'NC_000011.8' 'NW_004070890.2' 'NW_003871064.1' 'NW_004775427.1'
:  'NW_003871103.3' 'NT_187600.1' 'NT_187603.1' 'NW_004070883.1'
:  'NW_003871056.3' 'NW_003571064.2' 'NW_003571041.1' 'NW_004070872.2'
:  'NW_004070891.1' 'NC_000006.10' 'NC_000010.9' 'NW_004070877.1'
:  'NT_113793.3' 'NT_113796.3' 'NT_187576.1' 'NT_187594.1' 'NW_011332698.1'
:  'NT_187361.1' 'NT_187693.1' 'NW_011332701.1' 'NW_003871101.3'
:  'NW_003871065.1' 'NW_003315947.1' 'NW_004166863.1' 'NW_004504299.1'
:  'NW_003571040.1' 'NT_187661.1' 'NW_003571053.2' 'NW_003871086.1'
:  'NT_187633.1' 'NW_003871100.1' 'NW_003871058.1' 'NW_004070887.1'
:  'NW_009646209.1' 'NW_003315949.1' 'NW_003871099.1' 'NW_004070880.2'
:  'NW_003315932.1' 'NW_004775435.1' 'NW_004070882.1' 'NW_004775432.1'
:  'NT_187562.1' 'NT_187593.1' 'NW_003871096.1' 'NW_004504304.1'
:  'NW_003571048.1' 'NW_009646206.1' 'NW_003571049.1' 'NT_187513.1'
:  'NW_009646195.1' 'NW_009646198.1' 'NT_187653.1' 'NC_000004.10'
:  'NC_000015.8' 'NC_000007.12' 'NC_000017.9' 'NC_000005.8' 'NC_000016.8'
:  'NC_000022.9' 'NC_000008.9' 'NC_000020.9' 'NC_000012.10' 'NC_000014.7'
:  'NC_000009.10' 'NC_000024.8' 'NC_000019.8' 'NC_000013.9' 'NC_000018.8'
:  'NW_019805500.1' 'NW_015148969.2' 'NT_167222.1' 'NT_113889.1']

"Chromosome"
: Chromosome name/identifier including 1-22, X, Y, Mitochondrial and Unknown
: ['7' '15' '11' '14' '6' '2' '20' '10' '19' '16' '22' '12' '1' 'na' '8' '9'
:  '13' '21' '5' '4' '17' '18' '3' 'MT' 'Y' 'X' 'Un']

"Start"
:

"Stop"
:

"ReferenceAllele"
: The wild type nucleotide sequence of the variant.
: Examples: ['na' 'CTG' 'CGCGGGGCGGGG' 'T' 'ATTCT' '-' 'GGCCTG' 'AT'
:  'GGAAAGCATCTCTGGCTCACCATGTAA' 'G' 'GAGTTACAATTTCGATG' 'CC' 'C' 'GAG'
:  'TGA' 'CAG' 'A' 'GGC' 'TTG' 'AAAAT' 'AAAA']

"AlternateAllele"
: The nucleotide values of the variant.
: Examples: ['na' 'GG' 'ATAAATCACTTAGAGATGT' 'CTA' 'C(2_7)' '-' 'CA' 'AATTAAGGTATA'
:  'TCCCGGGTTCAAGCGATTCT' 'Alu' 'C(n)' 'G' 'TTTCCGACAAAGGT' 'CACAAAGTG' 'AC'
:  'TGACATCAGTCCGGGCAC' 'A' 'T' 'TC' 'CTTA' 'ACC' 'C' 'TTGAA' 'GTGG'
:  'AGTTACC' 'TCT' 'ATA' 'TG' 'TGG']

"Cytogenetic"
: The chromosomal location of the variant.
: Examples: ['7p22.1' '15q25.3' '11q24.2' ... '8p11.23-q11.21' '3p26.2-25.3'
:  '7q34-36.1']

"ReviewStatus"
: A short description indicating whether or not evaluation criteria are submitted, whether there is just one or 
: mutliple submitters, whether submissions are conflicting across submitters, and whether reviewed by
: an expert panel.
: Examples: ['criteria provided, single submitter' 'no assertion criteria provided'
:  'criteria provided, multiple submitters, no conflicts'
:  'criteria provided, conflicting interpretations'
:  'no interpretation for the single variant' 'practice guideline'
:  'reviewed by expert panel' 'no assertion provided']

"NumberSubmitters"
: How many submitters have uploaded an assertion for the variant.

"Guidelines"
: The guideline standard(s) applied to the assertion by the submitter.
: Examples: ['-' 'ACMG2021,ACMG2022' 'ACMG2022' 'ACMG2013,ACMG2016,ACMG2021,ACMG2022'
:  'ACMG2016,ACMG2021,ACMG2022' 'ACMG2013']

"TestedInGTR"
: TODO: validate description is accurate.
: Whether in genetic testing registry
: [ 'N' 'Y']

"OtherIDs"
:

"SubmitterCategories"
:

"VariationID"
: ClinVar assigns a unique integer identifier to each set of variants described in submitted records. The majority of submitted records in ClinVar interpret a single variant, and a Variation ID is assigned even if there is only one variant in the set. There are two subclasses of Variation IDs:
:   - those being interpreted directly (interpreted)
:   - those being interpreted only in the context of a set of variants (included)
: Used to link for VRS identifiers

"PositionVCF"
:

"ReferenceAlleleVCF"
:

"AlternateAlleleVCF"
:


### Ranges of values for GenCC and HP terms

#### Classification
```
GENCC:100001 Definitive
GENCC:100002 Strong
GENCC:100003 Moderate
GENCC:100004 Limited
GENCC:100005 Disputed Evidence
GENCC:100006 Refuted Evidence
GENCC:100008 No Known Disease Relationship
GENCC:100009 Supportive
```

#### Inheritance
: Either one-hot encode, and/or provide categories by user choice, or continuous
```
HP:0000006	Autosomal dominant
HP:0000007	Autosomal recessive
HP:0001417	X-linked
HP:0000005	Unknown
HP:0001450	Y-linked inheritance
HP:0001419	X-linked recessive
HP:0001423	X-linked dominant
HP:0012275	Autosomal dominant inheritance with maternal imprinting HP:0012275
HP:0001442	Somatic mosaicism
HP:0001427	Mitochondrial
HP:0012274	Autosomal dominant inheritance with paternal imprinting
HP:0010984	Digenic inheritance HP:0010984
HP:0032113	Semidominant
```

#### Submitters
```
GENCC:000101	Ambry Genetics
GENCC:000104	Genomics England PanelApp
GENCC:000105	Illumina
GENCC:000106	Invitae
GENCC:000108	Myriad Women’s Health
GENCC:000111	PanelApp Australia
GENCC:000112	TGMI|G2P
GENCC:000113	Franklin by Genoox
GENCC:000107	Laboratory for Molecular Medicine
GENCC:000114	King Faisal Specialist Hospital and Research Center
GENCC:000110	Orphanet
GENCC:000102	ClinGen
```



### The `submission_summary.txt` file is downloaded from the same directory as the variant summary.

"VariationID"
: the identifier assigned by ClinVar and used to build the URL, namely https://ncbi.nlm.nih.gov/clinvar/VariationID

"ClinicalSignificance"
: interpretation of the variation-condition relationship

"DateLastEvaluated"
: the last date the variation-condition relationship was evaluated by this submitter

"Description"
: an optional free text description of the basis of the interpretation

"SubmittedPhenotypeInfo"
: the name(s) or identifier(s)  submitted for the condition that was interpreted relative to the variant

"ReportedPhenotypeInfo"
: the MedGen identifier/name combinations ClinVar uses to report the condition that was interpreted. 'na' means there is no public identifer in MedGen for the condition.

"ReviewStatus"
: the level of review for this submission, namely http//www.ncbi.nlm.nih.gov/clinvar/docs/variation_report/#review_status

"CollectionMethod"
: the method by which the submitter obtained the information provided

"OriginCounts"
: the reported origin and the number of observations for each origin

"Submitter"
: the submitter of this record

"SCV"
: the accession and current version assigned by ClinVar to the submitted interpretation of the variation-condition relationship

"SubmittedGeneSymbol"
: the symbol provided by the submitter for the gene affected by the variant. May be null.

"ExplanationOfInterpretation"
: the submitter's preferred term for the interpretation when ClinicalSignificance is submitted as 'other' or 'drug response'. May be null.