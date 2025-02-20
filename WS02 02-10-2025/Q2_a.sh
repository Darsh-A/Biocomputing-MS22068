#!/bin/bash

count_nucleotides() {
  local sequence="$1"
  A_count=$(grep -o "A" <<< "$sequence" | wc -l)
  T_count=$(grep -o "T" <<< "$sequence" | wc -l)
  G_count=$(grep -o "G" <<< "$sequence" | wc -l)
  C_count=$(grep -o "C" <<< "$sequence" | wc -l)

  # Output the counts
  echo "A: $A_count, T: $T_count, G: $G_count, C: $C_count"
}

echo "Processing..."
echo "--------------------------"

sequence=""
header=""

while IFS= read -r line; do
  if [[ ${line:0:1} == ">" ]]; then
    if [[ -n "$sequence" ]]; then
      echo "$header"
      count_nucleotides "$sequence"
      echo 
    fi
    header="$line"
    sequence=""
  else
    sequence+="$line"
  fi
done < "fasta_file.txt"

if [[ -n "$sequence" ]]; then
  echo "$header"
  count_nucleotides "$sequence"
fi

echo "--------------------------"
echo "Done :3"
