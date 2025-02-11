#!/bin/bash

seq_count=0

while IFS= read -r line; do
  # Check if the line is a header
  if [[ ${line:0:1} == ">" ]]; then

    seq_count=$((seq_count + 1))

    # Only from second seq
    if [[ $seq_count -gt 1 ]]; then
      echo "Sequence $prev_seq_count Composition:"
      echo "A: $a_count"
      echo "T: $t_count"
      echo "G: $g_count"
      echo "C: $c_count"
        
      a_count=0
      t_count=0
      g_count=0
      c_count=0
    fi

    prev_seq_count=$seq_count

  else  # Its a seq line
    # Convert to uppercase to handle both cases
    line_upper=$(echo "$line" | tr '[:lower:]' '[:upper:]')

    for i in $(seq 0 $(( ${#line_upper} - 1 ))); do
      char="${line_upper:i:1}"
      case "$char" in
        A) a_count=$((a_count + 1)) ;;
        T) t_count=$((t_count + 1)) ;;
        G) g_count=$((g_count + 1)) ;;
        C) c_count=$((c_count + 1)) ;;
        *) echo "Warning: Invalid character '$char' in sequence $seq_count" ;; # Handle invalid chars
      esac
    done
  fi
done < "fasta_file.txt" # Inputs the fasta file

# Compute and print the composition of the last sequence
if [[ $seq_count -gt 0 ]]; then # Check if any sequences were found
    echo "Sequence $seq_count Composition:"
    echo "A: $a_count"
    echo "T: $t_count"
    echo "G: $g_count"
    echo "C: $c_count"
fi


echo "Total number of sequences: $seq_count"