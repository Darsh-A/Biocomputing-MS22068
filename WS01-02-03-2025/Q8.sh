#!/bin/bash

find_orfs() {
  sequence="$1"
  orfs=()

  for i in $(seq 0 $(( ${#sequence} - 3 ))); do
    codon="${sequence:i:3}"

    if [[ "$codon" == "ATG" || "$codon" == "GTG" ]]; then

      for j in $(seq $((i + 3)) $(( ${#sequence} - 3 ))); do
        stop_codon="${sequence:j:3}"
        if [[ "$stop_codon" == "TAG" || "$stop_codon" == "TAA" || "$stop_codon" == "TGA" ]]; then
          orf="${sequence:i:$((j - i + 3))}"
          orfs+=("$orf")
          break
        fi
      done
    fi
  done
  echo "${orfs[@]}"
}


while IFS= read -r line; do
  if [[ ${line:0:1} == ">" ]]; then
    echo "$line"
  else
    sequence="$line"
    orfs=$(find_orfs "$sequence")
    if [[ -n "$orfs" ]]; then
      for orf in $orfs; do
        echo "$orf"
      done
    else
      echo "No ORFs found."
    fi
  fi
done < "fasta_file.txt"