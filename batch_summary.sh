#!/bin/bash

# Check if the input file and output folder are provided as arguments
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <input_file> <output_folder>"
    exit 1
fi

# Input file containing variant IDs
input_file="$1"

# Output folder to store the results
output_folder="$2"

# Check if the input file exists
if [[ ! -f "$input_file" ]]; then
    echo "Error: File '$input_file' not found!"
    exit 1
fi

# Ensure the output directory exists
mkdir -p "$output_folder"

# Read the input file line by line
while IFS= read -r variant_id || [[ -n "$variant_id" ]]; do
    if [[ -n "$variant_id" ]]; then  # Ensure the line is not empty
        echo "Processing variant ID: $variant_id"
        python main.py --loglevel=info --expand \
            --sources="clinvar-submission-summary,clinvar-variant-summary,vrs,gencc-submissions,clingen-gene-disease,clingen-consensus-assertions-adult,clingen-consensus-assertions-pediatric,clingen-dosage,clingen-overall-scores-adult,clingen-overall-scores-pediatric" \
            --template --template-output="${output_folder}/variant_${variant_id}.txt" \
            --variant="$variant_id"
    fi
done < "$input_file"

echo "Processing complete. Results are saved in the '$output_folder' directory."
