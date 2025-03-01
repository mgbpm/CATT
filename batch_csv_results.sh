#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <input_file> <output_folder>"
    exit 1
fi

# Assign arguments to variables
INPUT_FILE="$1"
OUTPUT_FOLDER="$2"

# Ensure the output folder exists
mkdir -p "$OUTPUT_FOLDER"

# Define log level
LOGLEVEL="info"

# Loop through each variant ID in the file
while IFS= read -r VARIANT_ID; do
    echo "Generating summary for variant ID: $VARIANT_ID"

    # Run main.py in the current directory
    python main.py --loglevel=$LOGLEVEL --template \
        --sources="clinvar-submission-summary,clinvar-variant-summary,gencc-submissions,clingen-dosage,clingen-gene-disease,vrs" \
        --joined-output="${VARIANT_ID}.csv" --variant=$VARIANT_ID

    # Move the generated file to the output folder
    if [ -f "${VARIANT_ID}.csv" ]; then
        mv "${VARIANT_ID}.csv" "$OUTPUT_FOLDER/"
    else
        echo "Warning: File ${VARIANT_ID}.csv was not created!"
    fi
done < "$INPUT_FILE"

echo "Batch processing complete! Results stored in $OUTPUT_FOLDER"

