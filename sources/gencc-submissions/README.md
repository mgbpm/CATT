The file `gencc-submissions.tsv` can be downloaded from the GenCC website at `https://search.thegencc.org/download/action/submissions-export-tsv`. The file contains the following columns:

"uuid"
: A unique indentifier for gene-disease submission, of the form GENCC_`<submitter code`>-HGNC_`<hgnc code>`-OMIM_`<omim code>`-HP_`<human phenotype ontology inheritance code>`-GENCC_`<gencc classification code>`.

"gene_curie"
: The HGNC code for the gene, in the form HGNC:`<hgnc code>`.

"gene_symbol"
: The HGNC symbol for the gene.

"disease_curie"
: The Monarch Disease Ontology code for the disease association, in the form MONDO:`<mondo code>`.

"disease_title"
: The Monarch Disease Ontology disease name/title.

"disease_original_curie"
: The original Monarch Disease Ontology or OMIM code for the disease association, in the form MONDO:`<mondo code>` or OMIM:`<omim code>`.

"disease_original_title"
: The original Monarch Disease Ontology or OMIM disease name/title.

"classification_curie"
: The GenCC classification code, in the form GENCC:`<classification code>`.

"classification_title"
: The GenCC classification name/title.

"moi_curie"
: The mode of inheritance code, in the form HP:`<human phenotype ontology mode of inheritance code>`.

"moi_title"
: The mode of inheritance name/title.

"submitter_curie"
: The GenCC submitter code, in the form GENCC:`<code designating submitter>`.

"submitter_title"
: The GenCC submitter for the record.

"submitted_as_hgnc_id"
: The HGNC gene code as submitted.

"submitted_as_hgnc_symbol"
: The HGNC gene symbol as submitted.

"submitted_as_disease_id"
: The MONDO or OMIM disease code as submitted.

"submitted_as_disease_name"
: The MONDO or OMIM disease name as submitted.

"submitted_as_moi_id"
: The mode of inheritance code as submitted (Human Phenotype Ontology).

"submitted_as_moi_name"
: The mode of inheritance as submitted.

"submitted_as_submitter_id"
: The GenCC code of the record submitter.

"submitted_as_submitter_name"
: The record submitter.

"submitted_as_classification_id"
: The GenCC code of the classification as submitted.

"submitted_as_classification_name"
: The GenCC classification as submitted.

"submitted_as_date"
: The submission date of the record YYYY-MM-DD HH24:MI:SS format.

"submitted_as_public_report_url"
: An optional URL to a public record of the record from the submitter.

"submitted_as_notes"
: Free text notes in support of the assertion/classification.

"submitted_as_pmids"
: A comma-separated list of PubMED Id's for articles related to the classification/assertion.

"submitted_as_assertion_criteria_url"
: A URL (or PubMED Id) pointing to documentation of the criteria standard used for the classification/assertion of the submission.

"submitted_as_submission_id"
: An id created by the submitter associated to the specific assertion/classifcation of the record.

"submitted_run_date"
: The date the submission was added or updated to GenCC.


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
