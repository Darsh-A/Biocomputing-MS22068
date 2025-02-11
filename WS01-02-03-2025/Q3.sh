#!/bin/bash

read -p "till where:  " N

even_sum=0
odd_sum=0

for i in $(seq 1 $N); do

  if (( i % 2 == 0 )); then
    even_sum=$((even_sum + i))
  else
    odd_sum=$((odd_sum + i))
  fi
done

echo "Sum of even numbers: $even_sum"
echo "Sum of odd numbers: $odd_sum"