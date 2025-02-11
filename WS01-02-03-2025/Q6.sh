#!/bin/bash

read -p "Enter your word:  " WORD

length=${#WORD}
HALFWORD=${WORD:0:$((length/2))}
OTHERHALFWORD=${WORD:$((length/2)):length}

# Method 1 (The longer one uh)
REVWORD=""
for ((i=${#OTHERHALFWORD}-1; i>=0; i--)); do
    REVWORD=$REVWORD${OTHERHALFWORD:$i:1}
done

echo $REVWORD
echo $HALFWORD


if [[ "$REVWORD" == "$HALFWORD" ]]; then
    echo "Your word is a PALINDROME"
else
    echo "NOT A PALINDROME"
fi