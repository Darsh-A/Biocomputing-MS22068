#!/bin/bash

reverse_complement() {
  echo "$1" | rev | tr 'ATGCatgc' 'TACGtacg'
}

count_orfs() {
  local sequence="$1"
  local strand="$2"

  local orfs
  orfs=$(grep -o -P 'ATG(?:...)*?(?:TAA|TAG|TGA)' <<< "$sequence")

  local long_orf_count=0
  while IFS= read -r orf; do
    if [[ ${#orf} -gt 60 ]]; then
      ((long_orf_count++))
    fi
  done <<< "$orfs"

  echo "$strand strand: $long_orf_count ORFs longer than 20 codons"
}

fasta_file="fasta_file.txt"

echo "Processing FASTA file: $fasta_file"
echo "--------------------------"

sequence=""
header=""

while IFS= read -r line; do
  if [[ ${line:0:1} == ">" ]]; then
    if [[ -n "$sequence" ]]; then
      echo "$header"
      count_orfs "$sequence" "(+)"
      rev_comp=$(reverse_complement "$sequence")
      count_orfs "$rev_comp" "(-)"
      echo
    fi
    header="$line"
    sequence=""
  else
    sequence+="$line"
  fi
done < "$fasta_file"

if [[ -n "$sequence" ]]; then
  echo "$header"
  count_orfs "$sequence" "(+)"
  rev_comp=$(reverse_complement "$sequence")
  count_orfs "$rev_comp" "(-)"
fi

echo "--------------------------"
echo "Done."
