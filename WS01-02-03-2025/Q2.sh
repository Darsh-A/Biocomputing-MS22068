#!/bin/bash

# Predefined username and password : Usually stored in a DB
CORRECT_USER="admin"
CORRECT_PASS="password123"

ENTRY_ATTEMPTS=0
ALLOWED_ATTEMPTS=5

while [[ $ENTRY_ATTEMPTS -lt $ALLOWED_ATTEMPTS ]];
do
    # Prompt user for input
    read -p "Enter username: " input_user
    read -s -p "Enter password: " input_pass # -s tag for anonymous pass entry
    echo  # Move to a new line after password input

    # Check if the input matches the predefined credentials
    if [[ "$input_user" == "$CORRECT_USER" && "$input_pass" == "$CORRECT_PASS" ]]; then
        echo "Access Granted."
        break
    else
        ((ENTRY_ATTEMPTS++)) #Increment the Attempts var
        echo "Access Denied. Incorrect username or password."
        echo "Attempts left: $((ALLOWED_ATTEMPTS - ENTRY_ATTEMPTS))"
    fi
done

