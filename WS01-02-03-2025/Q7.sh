#!/bin/bash

complement() {
  case "$1" in
    A) echo "T";;
    T) echo "A";;
    G) echo "C";;
    C) echo "G";;
    a) echo "t";;
    t) echo "a";;
    g) echo "c";;
    c) echo "g";;
    *) echo "$1";;
  esac
}

output_file="complemented_fasta.txt"
> "$output_file"

echo "Processing..."

while IFS= read -r line; do
  if [[ ${line:0:1} == ">" ]]; then
    echo "$line" >> "$output_file"
  else 
    complement_seq=""
    for i in $(seq 0 $(( ${#line} - 1 ))); do
      char="${line:i:1}"
      complement_char=$(complement "$char")
      complement_seq+="$complement_char"
    done
    echo "$complement_seq" >> "$output_file"
  fi
done < "fasta_file.txt"

echo "Complemented sequence written to $output_file"