#!/bin/bash

# Check if the input file is provided as an argument
if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

# Input file containing variant IDs
input_file="$1"

# Check if the input file exists
if [[ ! -f "$input_file" ]]; then
    echo "Error: File '$input_file' not found!"
    exit 1
fi

# Ensure results directory exists
mkdir -p results

# Read the input file line by line
while IFS= read -r variant_id || [[ -n "$variant_id" ]]; do
    if [[ -n "$variant_id" ]]; then  # Ensure the line is not empty
        echo "Processing variant ID: $variant_id"
        python main.py --loglevel=info --expand \
            --sources="clinvar-submission-summary,clinvar-variant-summary,vrs,gencc-submissions,clingen-gene-disease,clingen-consensus-assertions-adult,clingen-consensus-assertions-pediatric,clingen-dosage,clingen-overall-scores-adult,clingen-overall-scores-pediatric" \
            --template --template-output="results/variant_${variant_id}.txt" \
            --variant="$variant_id"
    fi
done < "$input_file"

echo "Processing complete. Results are saved in the 'results/' directory."
