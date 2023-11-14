# clingen-ai-tools
Tools for preparing ClinGen, ClinVar and GenCC datasets for use in machine learning and LLM analysis.

Output is configured by user through parameters, where they can select from dictionary and type of output they want (one-hot, categorical, continuous, original text, etc.) linked across the sources.

# TODO's

- Determine if there are values that are equal to each other but different
  (e.g.) Pres Path = Lik Path
- For each categorical column determine if we create a continuous variable for at least a subset of the potential values
  (e.g.) Benign, Lik Ben, VUS, Lik Path, Path ==>  0, 1, 2, 3, 4
  - If there are possible values that are not on the continuum, determine what other fields are need to represent them (either one-hot or categorical)
    (e.g.) Likely Carrier; maybe create flag for does this express the phenotype or is it a carrier for the phenotype?
	(e.g.) Pharmacogenomic might need separate continuum
	(e.g.) Investigate what to put in continuous variable columns when the value doesn't apply, missing data
	- Some models handle missing data internally (Random Forest); others you need everything specified; gradient descent; 
	- Programatic options for how to deal with missing data
	- One-hot column for missing data (by column or row), value off the continuuum

- Create lists of unique values for each column (where appropriate)

- For next meeting:
  Review dictionaries and unique value sets
  Reach out to Larry to get access to the data from his tool (can get files?, mappings of codes?)

  
