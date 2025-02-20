#!/bin/bash

complement() {
  echo "$1" | tr 'ATGCatgc' 'TACGtacg' # using translate to convert the complement (This is so cool woa); no one character conditions hehe
}

output_file="complemented_fasta_new.txt"
> "$output_file"

echo "Processing..."

while IFS= read -r line; do
  if [[ ${line:0:1} == ">" ]]; then
    echo "$line" >> "$output_file"
  else
    complement_seq=$(complement "$line")
    echo "$complement_seq" >> "$output_file"
  fi
done < "fasta_file.txt"

echo "Complemented sequence written to $output_file"
